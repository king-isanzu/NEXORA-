import os
import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Flask, jsonify, request, g
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv

from selcom_client import create_selcom_checkout

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-production").encode()
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "24"))


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "nexora"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def make_token(user):
    header = {"alg": "HS256", "typ": "NEXORA"}
    payload = {
        "sub": int(user["id"]),
        "email": user["email"],
        "role": user.get("role", "customer"),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
    }
    encoded_header = b64url(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = b64url(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{encoded_header}.{encoded_payload}".encode()
    signature = hmac.new(JWT_SECRET, message, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{b64url(signature)}"


def read_token(token):
    try:
        header, payload, signature = token.split(".")
        message = f"{header}.{payload}".encode()
        expected = hmac.new(JWT_SECRET, message, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, b64url_decode(signature)):
            return None
        data = json.loads(b64url_decode(payload))
        if int(data.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return data
    except Exception:
        return None


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401
        token_data = read_token(header[7:].strip())
        if not token_data:
            return jsonify({"error": "Invalid or expired session."}), 401
        g.user_id = int(token_data["sub"])
        g.token_data = token_data
        return fn(*args, **kwargs)
    return wrapper


def hash_password(password):
    salt = secrets.token_bytes(16)
    n, r, p = 16384, 8, 1
    digest = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=64)
    return f"scrypt${n}${r}${p}${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    try:
        _, n, r, p, salt_hex, digest_hex = encoded.split("$")
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=64,
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def ensure_schema_and_seed():
    """Create small compatibility columns/data when the supplied SQL was imported."""
    db = get_db()
    cur = db.cursor()
    try:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'customer'")
        except mysql.connector.Error:
            pass

        cur.execute("SELECT id FROM businesses LIMIT 1")
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO businesses (name, category, phone, address) VALUES (%s,%s,%s,%s)",
                ("NEXORA Demo Store", "Food & Shopping", "+255700000000", "Dar es Salaam, Tanzania"),
            )
            business_id = cur.lastrowid
        else:
            cur.execute("SELECT id FROM businesses ORDER BY id LIMIT 1")
            business_id = cur.fetchone()[0]

        cur.execute("SELECT id FROM products LIMIT 1")
        if cur.fetchone() is None:
            products = [
                (business_id, "NEXORA Food Order", "Demo restaurant meal", 12000, 999),
                (business_id, "NEXORA Ice Cream", "Ice cream and dessert", 7000, 999),
                (business_id, "NEXORA Shopping Item", "General shopping item", 25000, 999),
            ]
            cur.executemany(
                "INSERT INTO products (business_id,name,description,price,stock) VALUES (%s,%s,%s,%s,%s)",
                products,
            )

        cur.execute("SELECT id FROM users WHERE email=%s", ("demo@nexora.co.tz",))
        if cur.fetchone() is None:
            cur.execute(
                """INSERT INTO users (full_name,email,phone,password_hash,address,role)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    "NEXORA Demo User",
                    "demo@nexora.co.tz",
                    "+255700000001",
                    hash_password("Demo@12345"),
                    "Dar es Salaam, Tanzania",
                    "customer",
                ),
            )
        db.commit()
    finally:
        cur.close()
        db.close()


def public_user(row):
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "address": row[4],
        "role": row[5] if len(row) > 5 else "customer",
    }


@app.get("/api/health")
def health():
    db_ok = False
    try:
        db = get_db(); cur = db.cursor(); cur.execute("SELECT 1"); cur.fetchone(); db_ok = True
        cur.close(); db.close()
    except Exception:
        pass
    return jsonify({"status": "ok", "service": "NEXORA API", "database": db_ok})


@app.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    required = ["name", "email", "phone", "password", "address"]
    if not all(str(data.get(x, "")).strip() for x in required):
        return jsonify({"error": "All registration fields are required."}), 400
    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    db = get_db(); cur = db.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email=%s OR phone=%s", (data["email"].strip().lower(), data["phone"].strip()))
        if cur.fetchone():
            return jsonify({"error": "Email or phone is already registered."}), 409
        cur.execute(
            "INSERT INTO users (full_name,email,phone,password_hash,address,role) VALUES (%s,%s,%s,%s,%s,'customer')",
            (data["name"].strip(), data["email"].strip().lower(), data["phone"].strip(), hash_password(data["password"]), data["address"].strip()),
        )
        db.commit()
        user_id = cur.lastrowid
        cur.execute("SELECT id,full_name,email,phone,address,role FROM users WHERE id=%s", (user_id,))
        user = public_user(cur.fetchone())
        return jsonify({"message": "Account created.", "user": user, "token": make_token(user)}), 201
    finally:
        cur.close(); db.close()


@app.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    identifier = str(data.get("identifier", "")).strip()
    password = str(data.get("password", ""))
    if not identifier or not password:
        return jsonify({"error": "Email/phone and password are required."}), 400

    db = get_db(); cur = db.cursor()
    try:
        cur.execute("SELECT id,full_name,email,phone,password_hash,address,role FROM users WHERE email=%s OR phone=%s LIMIT 1", (identifier.lower(), identifier))
        row = cur.fetchone()
        if not row or not verify_password(password, row[4]):
            return jsonify({"error": "Invalid login credentials."}), 401
        user = public_user((row[0], row[1], row[2], row[3], row[5], row[6]))
        return jsonify({"message": "Login successful.", "user": user, "token": make_token(user)})
    finally:
        cur.close(); db.close()


@app.get("/api/auth/me")
@auth_required
def me():
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("SELECT id,full_name,email,phone,address,role FROM users WHERE id=%s", (g.user_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"user": public_user(row)})
    finally:
        cur.close(); db.close()


@app.post("/api/auth/logout")
@auth_required
def logout():
    return jsonify({"message": "Logout acknowledged. Remove the token from the browser."})


@app.get("/api/products")
def products():
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,business_id,name,description,price,image_url,stock FROM products WHERE stock > 0 ORDER BY id")
        return jsonify({"products": cur.fetchall()})
    finally:
        cur.close(); db.close()


@app.post("/api/orders")
@auth_required
def create_order():
    data = request.get_json() or {}
    items = data.get("items", [])
    payment_method = str(data.get("payment_method", "")).strip()
    delivery_address = str(data.get("delivery_address", "")).strip()
    if not items or not payment_method:
        return jsonify({"error": "Cart items and payment method are required."}), 400

    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        total = 0
        validated = []
        for item in items:
            pid = int(item["product_id"])
            qty = max(1, int(item.get("quantity", 1)))
            cur.execute("SELECT id,name,price,stock FROM products WHERE id=%s", (pid,))
            product = cur.fetchone()
            if not product or product["stock"] < qty:
                return jsonify({"error": f"Product {pid} is unavailable."}), 400
            total += float(product["price"]) * qty
            validated.append((pid, qty, float(product["price"])))

        cur.execute(
            """INSERT INTO orders (user_id,total_amount,payment_method,status,delivery_address,latitude,longitude)
               VALUES (%s,%s,%s,'pending',%s,%s,%s)""",
            (g.user_id, total, payment_method, delivery_address, data.get("latitude"), data.get("longitude")),
        )
        order_id = cur.lastrowid
        for pid, qty, unit_price in validated:
            cur.execute("INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES (%s,%s,%s,%s)", (order_id,pid,qty,unit_price))
        db.commit()
        return jsonify({"message": "Order created.", "order_id": order_id, "amount": total, "status": "pending"}), 201
    finally:
        cur.close(); db.close()


@app.get("/api/orders")
@auth_required
def my_orders():
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,total_amount,payment_method,status,delivery_address,created_at FROM orders WHERE user_id=%s ORDER BY id DESC", (g.user_id,))
        return jsonify({"orders": cur.fetchall()})
    finally:
        cur.close(); db.close()


@app.post("/api/bookings")
@auth_required
def create_booking():
    data = request.get_json() or {}
    required = ["service_type", "booking_date", "booking_time"]
    if not all(data.get(x) for x in required):
        return jsonify({"error": "Booking information is incomplete."}), 400
    db = get_db(); cur = db.cursor()
    try:
        cur.execute(
            """INSERT INTO bookings (user_id,service_type,booking_date,booking_time,notes,status)
               VALUES (%s,%s,%s,%s,%s,'pending')""",
            (g.user_id, data["service_type"], data["booking_date"], data["booking_time"], data.get("notes", "")),
        )
        db.commit()
        return jsonify({"message": "Booking created.", "booking_id": cur.lastrowid}), 201
    finally:
        cur.close(); db.close()


@app.get("/api/bookings")
@auth_required
def my_bookings():
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,service_type,booking_date,booking_time,notes,status,created_at FROM bookings WHERE user_id=%s ORDER BY id DESC", (g.user_id,))
        return jsonify({"bookings": cur.fetchall()})
    finally:
        cur.close(); db.close()


@app.post("/api/delivery")
@auth_required
def create_delivery():
    data = request.get_json() or {}
    if not data.get("pickup_address") or not data.get("delivery_address"):
        return jsonify({"error": "Pickup and delivery addresses are required."}), 400
    db = get_db(); cur = db.cursor()
    try:
        cur.execute(
            """INSERT INTO delivery_orders (user_id,pickup_address,delivery_address,latitude,longitude,delivery_fee,status)
               VALUES (%s,%s,%s,%s,%s,%s,'pending')""",
            (g.user_id, data["pickup_address"], data["delivery_address"], data.get("latitude"), data.get("longitude"), float(data.get("delivery_fee", 0))),
        )
        db.commit()
        return jsonify({"message": "Delivery request created.", "delivery_id": cur.lastrowid}), 201
    finally:
        cur.close(); db.close()


@app.get("/api/delivery")
@auth_required
def my_delivery():
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,pickup_address,delivery_address,latitude,longitude,delivery_fee,status,created_at FROM delivery_orders WHERE user_id=%s ORDER BY id DESC", (g.user_id,))
        return jsonify({"deliveries": cur.fetchall()})
    finally:
        cur.close(); db.close()


@app.post("/api/addresses")
@auth_required
def save_address():
    data = request.get_json() or {}
    if not data.get("address_text"):
        return jsonify({"error": "Address is required."}), 400
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("INSERT INTO addresses (user_id,label,address_text,latitude,longitude) VALUES (%s,%s,%s,%s,%s)", (g.user_id,data.get("label","Default"),data["address_text"],data.get("latitude"),data.get("longitude")))
        db.commit()
        return jsonify({"message":"Address saved.","address_id":cur.lastrowid}),201
    finally:
        cur.close(); db.close()


@app.post("/api/payment/create")
@auth_required
def create_payment():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    method = str(data.get("method", "")).strip()
    if not order_id or not method:
        return jsonify({"error": "order_id and method are required."}), 400

    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,total_amount,payment_method FROM orders WHERE id=%s AND user_id=%s", (order_id,g.user_id))
        order = cur.fetchone()
        if not order:
            return jsonify({"error": "Order not found."}), 404

        amount = float(order["total_amount"])
        if method.lower() == "cash on delivery":
            cur.execute("INSERT INTO payments (order_id,provider,method,amount,status) VALUES (%s,'NEXORA',%s,%s,'pending')", (order_id,method,amount))
            db.commit()
            return jsonify({"message":"Cash on Delivery selected.","status":"pending","order_id":order_id})

        webhook = os.getenv("SELCOM_WEBHOOK_URL", f"{request.host_url.rstrip('/')}/api/payment/webhook")
        payload = {
            "order_id": str(order_id),
            "amount": amount,
            "method": method,
            "buyer_name": data.get("buyer_name", "NEXORA Customer"),
            "buyer_email": data.get("buyer_email", "customer@nexora.local"),
            "buyer_phone": data.get("buyer_phone", ""),
            "address": data.get("address", "Tanzania"),
            "no_of_items": int(data.get("no_of_items", 1)),
            "redirect_url": data.get("redirect_url", ""),
            "cancel_url": data.get("cancel_url", ""),
            "webhook": webhook,
        }
        response = create_selcom_checkout(payload)
        cur.execute("INSERT INTO payments (order_id,provider,method,amount,transaction_reference,status) VALUES (%s,'Selcom',%s,%s,%s,'pending')", (order_id,method,amount,str(response.get("order_id") or order_id)))
        db.commit()
        payment_url = response.get("payment_url") or response.get("checkout_url") or response.get("url")
        return jsonify({"message":"Payment checkout created.","payment_url":payment_url,"provider_response":response}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 503
    finally:
        cur.close(); db.close()


@app.post("/api/payment/webhook")
def payment_webhook():
    data = request.get_json(silent=True) or request.form.to_dict()
    order_id = data.get("order_id") or data.get("orderid")
    status = str(data.get("status") or data.get("payment_status") or "pending").lower()
    if not order_id:
        return jsonify({"error":"order_id missing"}),400
    normalized = "paid" if status in {"paid","success","successful","completed"} else "failed" if status in {"failed","cancelled","canceled"} else "pending"
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("UPDATE payments SET status=%s WHERE order_id=%s ORDER BY id DESC LIMIT 1", (normalized, order_id))
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", ("paid" if normalized == "paid" else "payment_failed" if normalized == "failed" else "pending", order_id))
        db.commit()
        return jsonify({"received": True})
    finally:
        cur.close(); db.close()


@app.errorhandler(Exception)
def unhandled(error):
    app.logger.exception(error)
    return jsonify({"error": "Server error. Check the backend terminal for details."}), 500

@app.get("/api/admin/orders")
@auth_required
def admin_get_orders():
    if g.token_data.get("role") != "admin":
        return jsonify({"error": "Ruhusa imekataliwa. Admin pekee."}), 403
    
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM orders ORDER BY id DESC")
        return jsonify({"orders": cur.fetchall()})
    finally:
        cur.close(); db.close()

@app.get("/api/admin/bookings")
@auth_required
def admin_get_bookings():
    if g.token_data.get("role") != "admin":
        return jsonify({"error": "Ruhusa imekataliwa. Admin pekee."}), 403
    
    db = get_db(); cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM bookings ORDER BY id DESC")
        return jsonify({"bookings": cur.fetchall()})
    finally:
        cur.close(); db.close()

if __name__ == "__main__":
    try:
        ensure_schema_and_seed()
    except Exception as exc:
        print("Database setup/seed warning:", exc)
        print("Import sql/nexora.sql into MySQL and check backend-python/.env")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
