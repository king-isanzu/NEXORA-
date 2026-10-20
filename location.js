async function useNexoraLocation() {
    const locationText = document.getElementById("locationText");
    const deliveryLocation = document.getElementById("deliveryLocation");
    if (!navigator.geolocation) {
        locationText.textContent = "Location unavailable";
        deliveryLocation.textContent = "Your browser does not support geolocation.";
        return;
    }
    locationText.textContent = "Detecting...";
    navigator.geolocation.getCurrentPosition(async position => {
        const { latitude, longitude, accuracy } = position.coords;
        const location = { latitude, longitude, accuracy, savedAt: new Date().toISOString() };
        localStorage.setItem("nexoraLocation", JSON.stringify(location));
        locationText.textContent = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
        deliveryLocation.textContent = `Location ready: ${latitude.toFixed(6)}, ${longitude.toFixed(6)} (accuracy ±${Math.round(accuracy)}m)`;

        const token = localStorage.getItem("nexoraToken");
        const user = JSON.parse(localStorage.getItem("nexoraUser") || "null");
        if (token && user) {
            try {
                await fetch("http://localhost:5000/api/addresses", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ label: "Current location", address_text: user.address || "GPS location", latitude, longitude })
                });
            } catch (error) { console.warn("Could not save location", error); }
        }
    }, error => {
        locationText.textContent = "Set location";
        deliveryLocation.textContent = "Location permission was not granted. You can enter an address manually.";
        console.warn("Location error:", error.message);
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 });
}
