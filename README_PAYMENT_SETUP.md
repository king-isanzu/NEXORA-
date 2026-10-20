# NEXORA — Real Payment Gateway Setup

NEXORA now has a server-side Selcom checkout integration. The browser never receives the Selcom secret.

## What is integrated

- Frontend payment buttons call `http://localhost:5000/api/payment/create`.
- Python/Flask creates a Selcom hosted checkout order.
- The customer is redirected to the Selcom payment page.
- Selcom can handle the supported mobile-money/card channels available to the merchant account.
- A webhook endpoint is included at `/api/payment/webhook` for payment notifications.

## Important: credentials are required

The code cannot perform a real transaction until NEXORA has an authorized Selcom merchant/developer account and credentials. Selcom's official developer documentation says API credentials are obtained from the developer/business account, and its Tanzania documentation describes ecommerce checkout and mobile-money/card flows.

Copy:

```text
backend-python/.env.example
```

to:

```text
backend-python/.env
```

Then fill in:

```text
SELCOM_BASE_URL=...
SELCOM_API_KEY=...
SELCOM_API_SECRET=...
SELCOM_VENDOR=...
SELCOM_WEBHOOK_URL=...
```

Do NOT put API secrets in `frontend/payment.js`.

## Run the backend

Open a terminal in:

```text
NEXORA_FINAL/backend-python
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start Flask:

```powershell
python app.py
```

The API runs on:

```text
http://localhost:5000
```

## Run the frontend

In a second terminal, open:

```text
NEXORA_FINAL/frontend
```

Run:

```powershell
python -m http.server 5500
```

Open:

```text
http://localhost:5500
```

## Local webhook limitation

A payment provider cannot normally call `http://localhost:5000` from the public internet. For production webhooks, use a public HTTPS domain/tunnel and put that URL in `SELCOM_WEBHOOK_URL`.

## Security

The project intentionally does not collect or store customer mobile-money PINs or card PAN/CVV. The customer enters sensitive payment information on the authorized provider's checkout flow.
