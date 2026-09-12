"""
Intégration crypto via NOWPayments (accepte BTC, ETH, USDT, etc.).
Doc : https://documenter.getpostman.com/view/7907941/S1a32n38
Alternative possible : Coinbase Commerce.
"""
import requests
from config import NOWPAYMENTS_API_KEY, PUBLIC_BASE_URL

BASE_URL = "https://api.nowpayments.io/v1"
HEADERS = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}


def create_invoice(amount_usd, donation_id):
    """Crée une facture crypto et retourne l'URL de paiement hébergée par NOWPayments."""
    payload = {
        "price_amount": amount_usd,
        "price_currency": "usd",
        "order_id": str(donation_id),
        "order_description": f"Don #{donation_id}",
        "ipn_callback_url": f"{PUBLIC_BASE_URL}/webhook/crypto",
        "success_url": f"{PUBLIC_BASE_URL}/thanks",
        "cancel_url": f"{PUBLIC_BASE_URL}/cancel",
    }
    resp = requests.post(f"{BASE_URL}/invoice", json=payload, headers=HEADERS, timeout=15)
    data = resp.json()
    if "invoice_url" in data:
        return {"ok": True, "payment_url": data["invoice_url"], "invoice_id": data["id"]}
    return {"ok": False, "error": data}
