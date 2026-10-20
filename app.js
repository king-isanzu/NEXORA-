const API_BASE = "http://localhost:5000/api";
let cart = JSON.parse(localStorage.getItem("nexoraCart") || "[]");

function money(value) {
    return new Intl.NumberFormat("en-TZ").format(value);
}

function token() {
    return localStorage.getItem("nexoraToken") || "";
}

function currentUser() {
    try { return JSON.parse(localStorage.getItem("nexoraUser") || "null"); }
    catch { return null; }
}

function authHeaders(extra = {}) {
    return token() ? { ...extra, Authorization: `Bearer ${token()}` } : extra;
}

function requireLogin() {
    if (token()) return true;
    document.getElementById("loginModal").classList.remove("hidden");
    document.getElementById("authMessage").textContent = "Please login first to continue.";
    return false;
}

function saveCart() {
    localStorage.setItem("nexoraCart", JSON.stringify(cart));
    renderCart();
}

function addDemoItem(productId, name, price) {
    const existing = cart.find(item => item.productId === productId);
    if (existing) existing.quantity += 1;
    else cart.push({ id: Date.now(), productId, name, price, quantity: 1 });
    saveCart();
    document.getElementById("checkout").scrollIntoView({ behavior: "smooth" });
}

function removeCartItem(id) {
    cart = cart.filter(item => item.id !== id);
    saveCart();
}

function renderCart() {
    const cartItems = document.getElementById("cartItems");
    const cartCount = document.getElementById("cartCount");
    const cartTotal = document.getElementById("cartTotal");
    cartCount.textContent = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
    if (!cart.length) {
        cartItems.innerHTML = '<p class="empty">Your cart is empty.</p>';
        cartTotal.textContent = "TZS 0";
        return;
    }
    let total = 0;
    cartItems.innerHTML = cart.map(item => {
        const qty = item.quantity || 1;
        total += Number(item.price) * qty;
        return `<div class="cart-item">
            <div><strong>${item.name}</strong><div class="small-note">TZS ${money(item.price)} × ${qty}</div></div>
            <button class="outline-btn" onclick="removeCartItem(${item.id})">Remove</button>
        </div>`;
    }).join("");
    cartTotal.textContent = `TZS ${money(total)}`;
}

function openBooking(service) {
    if (!requireLogin()) return;
    document.getElementById("bookingService").value = service;
    document.getElementById("bookings").scrollIntoView({ behavior: "smooth" });
}

function openDelivery() {
    if (!requireLogin()) return;
    document.getElementById("delivery").scrollIntoView({ behavior: "smooth" });
}

function filterServices(text) {
    const query = text.toLowerCase().trim();
    document.querySelectorAll(".service-card").forEach(card => {
        const searchable = card.dataset.search.toLowerCase();
        card.style.display = !query || searchable.includes(query) ? "" : "none";
    });
}

function setupSearch() {
    const input = document.getElementById("searchInput");
    document.getElementById("searchButton").addEventListener("click", () => {
        filterServices(input.value);
        document.getElementById("services").scrollIntoView({ behavior: "smooth" });
    });
    input.addEventListener("keydown", event => {
        if (event.key === "Enter") document.getElementById("searchButton").click();
    });
    document.querySelectorAll("[data-category]").forEach(button => {
        button.addEventListener("click", () => {
            input.value = button.dataset.category;
            filterServices(button.dataset.category);
            document.getElementById("services").scrollIntoView({ behavior: "smooth" });
        });
    });
}

    function updateAuthUI() {
    const token = localStorage.getItem('nexoratokent');
    const userJson = localStorage.getItem('nexorauser');
    const loginBtn = document.getElementById('openLoginButton');
    const adminBtn = document.getElementById('adminButton');

    if (token && userJson) {
        const user = JSON.parse(userJson);
        
        if (loginBtn) {
            loginBtn.textContent = "Logout";
            loginBtn.onclick = logout; 
        }

        if (user.role === 'admin') {
            if (adminBtn) adminBtn.style.display = 'inline-block';
        } else {
            if (adminBtn) adminBtn.style.display = 'none';
        }
    } else {
        if (loginBtn) {
            loginBtn.textContent = "Login";
            loginBtn.onclick = () => document.getElementById('loginModal').classList.remove('hidden');
        }
        if (adminBtn) adminBtn.style.display = 'none';
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('openLoginButton');
    
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            document.getElementById('loginModal').classList.remove('hidden');
        });
    }
});
document.addEventListener('DOMContentLoaded', () => {
    // 1. Kitufe cha Login kikuu
    const loginBtn = document.getElementById('openLoginButton');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            document.getElementById('loginModal').classList.remove('hidden');
        });
    }

    // 2. Kitufe cha Demo Account
    const demoBtn = document.getElementById('demoLoginButton');
    if (demoBtn) {
        demoBtn.addEventListener('click', async () => {
            try {
                // Tunatumia function yako ya login iliyopo na hizi credentials za demo
                await login('demo@nexora.co.tz', 'Demo@12345');
                
                // Kama imefanikiwa, funga ile dirisha la Login
                document.getElementById('loginModal').classList.add('hidden');
                
                // Onyesha ujumbe wa mafanikio
                alert("Hongera! Umeingia kama Demo User.");
                
            } catch (error) {
                // Kama kuna kosa (mfano database haipo), ionyeshe kwenye modal
                document.getElementById('authMessage').textContent = "Kosa: " + error.message;
                document.getElementById('authMessage').style.color = "red";
            }
        });
    }
});
// 3. Kitufe cha Kufungua Register Modal
const openRegisterBtn = document.getElementById('openRegisterButton');
if (openRegisterBtn) {
    openRegisterBtn.addEventListener('click', () => {
        document.getElementById('loginModal').classList.add('hidden'); // Ficha Login
        document.getElementById('registerModal').classList.remove('hidden'); // Fungua Register
    });
}

// 4. Kitufe cha Kufunga Register Modal
const closeRegisterBtn = document.getElementById('closeRegisterButton');
if (closeRegisterBtn) {
    closeRegisterBtn.addEventListener('click', () => {
        document.getElementById('registerModal').classList.add('hidden');
    });
}

// 5. Kusimamia Fomu ya Kujisajili (Register Form)
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Zuia ukurasa usirefresh

        // Chukua taarifa zote kwenye fomu
        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const phone = document.getElementById('registerPhone').value;
        const password = document.getElementById('registerPassword').value;
        const address = document.getElementById('registerAddress').value;

        try {
            // Tuma taarifa kwenye Backend yako
            const response = await fetch('http://localhost:5000/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, phone, password, address })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Usajili umeshindikana.");
            }

            // Kama usajili umefanikiwa
            document.getElementById('registerMessage').textContent = "Akaunti imefunguliwa! Sasa unaweza kuingia.";
            document.getElementById('registerMessage').style.color = "lightgreen";
            
            // Unaweza kumuingiza moja kwa moja hapa, lakini ni bora umwambie aingie
            setTimeout(() => {
                document.getElementById('registerModal').classList.add('hidden');
                document.getElementById('loginModal').classList.remove('hidden');
            }, 2000);

        } catch (error) {
            document.getElementById('registerMessage').textContent = "Kosa: " + error.message;
            document.getElementById('registerMessage').style.color = "red";
        }
    });
}