# NEXORA FINAL

Everything You Need, One Place.

## 1. Project structure

NEXORA_FINAL/
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── location.js
│   ├── payment.js
│   └── assets/
│       └── nexora-main.png
│
├── backend-python/
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
│
├── sql/
│   └── nexora.sql
│
└── docs/
    └── README.md


## 2. Frontend

Open:

frontend/index.html

For best results in VS Code, use Live Server.

The supplied NEXORA image is used as:
- Main hero image
- Login image


## 3. MySQL

Create the database using:

sql/nexora.sql

The schema contains:
- users
- businesses
- products
- orders
- order_items
- bookings
- addresses
- delivery_orders
- payments
- reviews

The database uses InnoDB, foreign keys and indexes.


## 4. Python backend

Open terminal inside:

backend-python

Install:

pip install -r requirements.txt

Copy:

.env.example

to:

.env

Then put your MySQL password in .env.

Run:

python app.py

API:

http://localhost:5000/api/health


## 5. Important payment note

The UI contains:

Mobile Money:
- M-Pesa
- Airtel Money
- Mixx by Yas
- HaloPesa

Banks:
- NMB
- CRDB
- Stanbic
- NBC
- Absa
- KCB
- Equity
- DTB
- I&M Bank
- NCBA
- Exim Bank
- Standard Chartered
- Other Bank

Cards:
- Visa
- Mastercard

Other:
- Selcom
- Cash on Delivery

These are payment choices in the UI.

Real transactions are NOT activated by this demo.
For production, connect the authorized provider APIs/gateway on the backend.
Never collect or store bank passwords, ATM PINs or mobile-money PINs.


## 6. Location

The browser geolocation API is used by location.js.

The user must grant browser location permission.

For production delivery, connect the coordinates to:
- address lookup/geocoding
- delivery fee calculation
- driver assignment
- order tracking


## 7. Security before production

Do not store plain-text passwords.

Use password hashing such as bcrypt/Argon2.

Use HTTPS.

Store secrets in environment variables.

Add authentication tokens/sessions.

Validate every backend request.

Add payment-provider webhooks.

Add admin/business dashboards.

Add rate limiting and audit logs.


## 8. Suggested production modules

Customer:
- account
- cart
- checkout
- orders
- bookings
- addresses
- reviews

Business:
- products
- services
- availability
- bookings
- order management

Delivery:
- driver
- pickup
- destination
- status
- location tracking

Admin:
- users
- businesses
- products
- orders
- payments
- reports


## 9. Run order

1. Install MySQL.
2. Run sql/nexora.sql.
3. Configure backend .env.
4. Install Python packages.
5. Run python app.py.
6. Open frontend/index.html using VS Code Live Server.
7. Test the demo.
8. Add real provider credentials only on the secure backend.

## Payment integration

The latest package includes a Selcom server-side checkout integration. Real payments require an authorized Selcom merchant/developer account and credentials in `backend-python/.env`. See `README_PAYMENT_SETUP.md`.


## Real authentication and backend

The current build uses the Python/Flask backend + MySQL for registration, login, session tokens, orders, bookings, delivery requests, addresses and payment records. Passwords are stored as salted scrypt hashes; plaintext passwords are never stored.

### Demo account
- Email: `demo@nexora.co.tz`
- Password: `Demo@12345`

The backend creates this demo account automatically when the `nexora` database is available. Change/remove it before production.

### Run
1. Import `sql/nexora.sql` into MySQL.
2. Copy `backend-python/.env.example` to `backend-python/.env` and set your MySQL values.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start API: `python app.py`
5. In another terminal, run the frontend: `cd frontend` then `python -m http.server 5500`
6. Open `http://localhost:5500`

### Real payments
Selcom credentials are server-side only. Put your authorized merchant/sandbox credentials in `.env`. The frontend never receives the API secret.
