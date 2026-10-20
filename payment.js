let selectedPayment = "";
const PAYMENT_API_BASE = "http://localhost:5000/api";

function selectPayment(method) {
    selectedPayment = method;
    document.querySelectorAll(".payment-option").forEach(button => {
        button.classList.toggle("selected", button.dataset.payment === method);
    });
    document.getElementById("selectedPayment").textContent = `Selected payment: ${method}`;
}

function selectBank(bank) {
    if (!bank) return;
    selectedPayment = `Bank — ${bank}`;
    document.querySelectorAll(".payment-option").forEach(button => button.classList.remove("selected"));
    document.getElementById("selectedPayment").textContent = `Selected payment: ${selectedPayment}`;
}

function getCartAmount() {
    const text = document.getElementById("cartTotal").textContent || "0";
    return Number(text.replace(/[^0-9.]/g, "")) || 0;
}

async function startPayment() {
    const token = localStorage.getItem("nexoraToken");
    if (!token) {
        document.getElementById("loginModal").classList.remove("hidden");
        document.getElementById("authMessage").textContent = "Login is required before checkout.";
        return;
    }
    if (!selectedPayment) return alert("Please select a payment method.");
    if (!window.cart?.length && !JSON.parse(localStorage.getItem("nexoraCart") || "[]").length) return alert("Your cart is empty.");

    const cart = JSON.parse(localStorage.getItem("nexoraCart") || "[]");
    const amount = getCartAmount();
    const user = JSON.parse(localStorage.getItem("nexoraUser") || "{}");
    const location = JSON.parse(localStorage.getItem("nexoraLocation") || "null");
    const orderPayload = {
        items: cart.map(item => ({ product_id: item.productId, quantity: item.quantity || 1 })),
        payment_method: selectedPayment,
        delivery_address: user.address || "Tanzania",
        latitude: location?.latitude,
        longitude: location?.longitude
    };

    const payButton = document.getElementById("payButton");
    payButton.disabled = true;
    payButton.textContent = "Creating order...";
    try {
        const orderResponse = await fetch(`${PAYMENT_API_BASE}/orders`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(orderPayload)
        });
        const order = await orderResponse.json();
        if (!orderResponse.ok) throw new Error(order.error || "Order creation failed.");

        payButton.textContent = "Connecting payment...";
        const paymentResponse = await fetch(`${PAYMENT_API_BASE}/payment/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                order_id: order.order_id,
                amount,
                method: selectedPayment,
                buyer_name: user.name,
                buyer_email: user.email,
                buyer_phone: user.phone,
                address: user.address || "Tanzania",
                no_of_items: cart.reduce((sum, item) => sum + (item.quantity || 1), 0),
                redirect_url: `${window.location.origin}${window.location.pathname}?payment=success`,
                cancel_url: `${window.location.origin}${window.location.pathname}?payment=cancelled`
            })
        });
        const result = await paymentResponse.json();
        if (!paymentResponse.ok) throw new Error(result.error || "Payment request failed.");

        if (result.payment_url) {
            window.location.href = result.payment_url;
            return;
        }
        localStorage.removeItem("nexoraCart");
        alert(result.message || "Payment request created.");
        location.reload();
    } catch (error) {
        alert(`Checkout failed.\n\n${error.message}`);
    } finally {
        payButton.disabled = false;
        payButton.textContent = "Continue to Payment";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".payment-option").forEach(button => button.addEventListener("click", () => selectPayment(button.dataset.payment)));
    document.getElementById("bankPayment").addEventListener("change", event => selectBank(event.target.value));
    document.getElementById("payButton").addEventListener("click", startPayment);
    const params = new URLSearchParams(window.location.search);
    if (params.get("payment") === "success") alert("Payment returned successfully. Final status is confirmed by the backend webhook.");
    if (params.get("payment") === "cancelled") alert("Payment was cancelled.");
});
