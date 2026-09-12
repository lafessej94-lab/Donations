"""
Serveur FastAPI qui reçoit les notifications de paiement de CinetPay, PayPal et
NOWPayments, met à jour la base de données, puis déclenche les notifications
Telegram (annonce publique + alerte au donateur).

Lancer avec : uvicorn webhook_server:app --host 0.0.0.0 --port 8000
En local, exposer avec ngrok et mettre l'URL dans PUBLIC_BASE_URL (.env).
"""
import hashlib
import hmac
import json
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

import database as db
from config import NOWPAYMENTS_IPN_SECRET
from payments import cinetpay, paypal
from notifier import notify_donation_confirmed  # défini dans bot.py / notifier.py

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhook")

app = FastAPI(title="DonBot Webhooks")


@app.post("/webhook/cinetpay")
async def cinetpay_webhook(request: Request):
    form = await request.form()
    transaction_id = form.get("cpm_trans_id") or form.get("transaction_id")
    if not transaction_id:
        raise HTTPException(400, "transaction_id manquant")

    # Ne jamais faire confiance au contenu du webhook seul : on revérifie côté API.
    if cinetpay.verify_payment(transaction_id):
        donation = db.mark_paid(provider_ref=transaction_id)
        if donation:
            await notify_donation_confirmed(donation)
        return PlainTextResponse("OK")
    else:
        db.mark_failed(provider_ref=transaction_id)
        return PlainTextResponse("FAILED")


@app.get("/webhook/paypal/return")
async def paypal_return(donation_id: int, token: str):
    """PayPal redirige ici après approbation ; `token` = order_id."""
    success, data = paypal.capture_order(token)
    if success:
        donation = db.mark_paid(donation_id=donation_id)
        db.set_provider_ref(donation_id, token)
        if donation:
            await notify_donation_confirmed(donation)
        return PlainTextResponse("Merci pour votre don ! Vous pouvez retourner sur Telegram.")
    db.mark_failed(donation_id=donation_id)
    return PlainTextResponse("Le paiement PayPal a échoué ou a été annulé.")


@app.get("/webhook/paypal/cancel")
async def paypal_cancel(donation_id: int):
    db.mark_failed(donation_id=donation_id)
    return PlainTextResponse("Paiement annulé.")


def _verify_nowpayments_signature(raw_body: bytes, signature: str) -> bool:
    sorted_body = json.dumps(json.loads(raw_body), sort_keys=True, separators=(",", ":"))
    expected = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode(), sorted_body.encode(), hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


@app.post("/webhook/crypto")
async def crypto_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("x-nowpayments-sig", "")

    if not _verify_nowpayments_signature(raw_body, signature):
        raise HTTPException(401, "Signature invalide")

    payload = json.loads(raw_body)
    donation_id = int(payload.get("order_id"))
    status = payload.get("payment_status")

    if status in ("finished", "confirmed"):
        donation = db.mark_paid(donation_id=donation_id)
        if donation:
            await notify_donation_confirmed(donation)
    elif status in ("failed", "expired", "refunded"):
        db.mark_failed(donation_id=donation_id)

    return PlainTextResponse("OK")


@app.get("/thanks")
async def thanks():
    return PlainTextResponse("Merci pour votre don ! Retournez sur Telegram pour voir la confirmation.")


@app.get("/cancel")
async def cancel():
    return PlainTextResponse("Paiement annulé.")
