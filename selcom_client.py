import base64
import os


def b64(value: str) -> str:
    return base64.b64encode(value.encode('utf-8')).decode('ascii')


def create_selcom_checkout(payload: dict):
    """Create a Selcom hosted checkout order.

    Credentials are read from environment variables and are never sent to the browser.
    The exact Selcom base URL/vendor/API credentials are supplied by Selcom for the
    merchant account/sandbox.
    """
    try:
        from selcom_apigw_client import apigwClient
    except ImportError as exc:
        raise RuntimeError(
            "Selcom SDK is not installed. Run: pip install selcom_apigw_client"
        ) from exc

    base_url = os.getenv('SELCOM_BASE_URL', '').strip()
    api_key = os.getenv('SELCOM_API_KEY', '').strip()
    api_secret = os.getenv('SELCOM_API_SECRET', '').strip()
    vendor = os.getenv('SELCOM_VENDOR', '').strip()

    if not all([base_url, api_key, api_secret, vendor]):
        raise RuntimeError(
            'Selcom is not configured. Set SELCOM_BASE_URL, SELCOM_API_KEY, '
            'SELCOM_API_SECRET and SELCOM_VENDOR in backend-python/.env.'
        )

    client = apigwClient.Client(base_url, api_key, api_secret)

    order = {
        'vendor': vendor,
        'order_id': payload['order_id'],
        'buyer_email': payload.get('buyer_email', 'customer@nexora.local'),
        'buyer_name': payload.get('buyer_name', 'NEXORA Customer'),
        'buyer_phone': payload.get('buyer_phone', ''),
        'amount': int(round(float(payload['amount']))),
        'currency': 'TZS',
        'payment_methods': 'ALL',
        'redirect_url': b64(payload['redirect_url']),
        'cancel_url': b64(payload['cancel_url']),
        'webhook': b64(payload['webhook']),
        'billing.firstname': payload.get('buyer_name', 'NEXORA').split(' ')[0],
        'billing.lastname': 'Customer',
        'billing.address_1': payload.get('address', 'Tanzania'),
        'billing.city': 'Dar es Salaam',
        'billing.country': 'TZ',
        'billing.email': payload.get('buyer_email', 'customer@nexora.local'),
        'billing.phone': payload.get('buyer_phone', ''),
        'buyer_remarks': 'NEXORA online order',
        'merchant_remarks': payload['order_id'],
        'no_of_items': int(payload.get('no_of_items', 1)),
    }

    response = client.postFunc('/v1/checkout/create-order', order)
    return response
