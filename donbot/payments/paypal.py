"""
Intégration PayPal via l'API REST Orders v2.
Doc : https://developer.paypal.com/docs/api/orders/v2/
"""
import requests
from config import PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_MODE, PUBLIC_BASE_URL

BASE_URL = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"


def _get_access_token():
    resp = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_order(amount_usd, donation_id):
    """Crée une commande PayPal et retourne le lien d'approbation à donner à l'utilisateur."""
    token = _get_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": str(donation_id),
            "amount": {"currency_code": "USD", "value": f"{amount_usd:.2f}"},
            "description": f"Don #{donation_id}",
        }],
        "application_context": {
            "return_url": f"{PUBLIC_BASE_URL}/webhook/paypal/return?donation_id={donation_id}",
            "cancel_url": f"{PUBLIC_BASE_URL}/webhook/paypal/cancel?donation_id={donation_id}",
            "user_action": "PAY_NOW",
        },
    }
    resp = requests.post(
        f"{BASE_URL}/v2/checkout/orders",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    data = resp.json()
    approve_link = next((l["href"] for l in data.get("links", []) if l["rel"] == "approve"), None)
    if approve_link:
        return {"ok": True, "approve_url": approve_link, "order_id": data["id"]}
    return {"ok": False, "error": data}


def capture_order(order_id):
    """Capture les fonds une fois que l'utilisateur a approuvé le paiement côté PayPal."""
    token = _get_access_token()
    resp = requests.post(
        f"{BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    data = resp.json()
    return data.get("status") == "COMPLETED", data
