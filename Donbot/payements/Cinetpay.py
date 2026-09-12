"""
Intégration CinetPay : couvre MTN Money, Airtel Money, Moov Money et Wave
via un seul compte marchand. Documentation : https://docs.cinetpay.com

Flux :
1. On appelle /v2/payment pour générer un lien de paiement.
2. L'utilisateur paie sur la page CinetPay (choix de son opérateur).
3. CinetPay appelle notre webhook (notify_url) -> on vérifie via /v2/payment/check.
"""
import requests
import uuid
from config import CINETPAY_API_KEY, CINETPAY_SITE_ID, CINETPAY_CURRENCY, PUBLIC_BASE_URL

BASE_URL = "https://api-checkout.cinetpay.com/v2"


def create_payment(amount, description, donation_id, customer_name="Donateur"):
    """
    Crée une transaction CinetPay et retourne l'URL de paiement à envoyer à l'utilisateur.
    `donation_id` est réutilisé comme transaction_id pour faire le lien avec notre DB.
    """
    transaction_id = f"don-{donation_id}-{uuid.uuid4().hex[:6]}"

    payload = {
        "apikey": CINETPAY_API_KEY,
        "site_id": CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
        "amount": int(amount),
        "currency": CINETPAY_CURRENCY,
        "description": description,
        "notify_url": f"{PUBLIC_BASE_URL}/webhook/cinetpay",
        "return_url": f"{PUBLIC_BASE_URL}/thanks",
        "channels": "MOBILE_MONEY",  # inclut MTN, Airtel, Moov, Wave selon le pays
        "customer_name": customer_name,
    }

    resp = requests.post(f"{BASE_URL}/payment", json=payload, timeout=15)
    data = resp.json()

    if data.get("code") == "201":
        return {
            "ok": True,
            "payment_url": data["data"]["payment_url"],
            "transaction_id": transaction_id,
        }
    return {"ok": False, "error": data.get("message", "Erreur CinetPay inconnue")}


def verify_payment(transaction_id):
    """Vérifie le statut réel d'une transaction (à appeler depuis le webhook, jamais faire confiance
    aveuglément au contenu du webhook lui-même)."""
    payload = {
        "apikey": CINETPAY_API_KEY,
        "site_id": CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
    }
    resp = requests.post(f"{BASE_URL}/payment/check", json=payload, timeout=15)
    data = resp.json()

    if data.get("code") == "00" and data["data"].get("status") == "ACCEPTED":
        return True
    return False
