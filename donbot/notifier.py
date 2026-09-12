"""
Pont entre le serveur webhook (FastAPI) et le bot Telegram (python-telegram-bot).
On garde une référence globale au `Bot` initialisé dans bot.py pour pouvoir
envoyer des messages depuis les routes webhook.
"""
from telegram import Bot
from telegram.constants import ParseMode

import database as db
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, ANNOUNCE_CHAT_ID

_bot = Bot(token=TELEGRAM_BOT_TOKEN)


def format_progress_bar(current, target, length=20):
    ratio = min(current / target, 1.0) if target else 0
    filled = int(length * ratio)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {ratio*100:.1f}%"


async def notify_donation_confirmed(donation: dict):
    """Appelé quand un don passe au statut 'paid'. Annonce publiquement + alerte l'admin."""
    goal = db.get_goal()
    total = db.get_total_paid()

    donor = donation.get("username") or f"Utilisateur {donation['telegram_user_id']}"
    amount = donation["amount"]
    currency = donation["currency"]

    bar = format_progress_bar(total, goal["target_amount"])

    public_msg = (
        f"🎉 *Nouveau don reçu !*\n"
        f"👤 {donor}\n"
        f"💰 {amount:,.0f} {currency} via {donation['method'].upper()}\n\n"
        f"🎯 Objectif : {total:,.0f} / {goal['target_amount']:,.0f} {goal['currency']}\n"
        f"{bar}"
    )

    if ANNOUNCE_CHAT_ID:
        await _bot.send_message(chat_id=ANNOUNCE_CHAT_ID, text=public_msg, parse_mode=ParseMode.MARKDOWN)

    if ADMIN_CHAT_ID:
        await _bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"✅ Don confirmé #{donation['id']} — {amount} {currency} ({donation['method']})",
        )

    # Notifier aussi directement le donateur en privé
    try:
        await _bot.send_message(
            chat_id=donation["telegram_user_id"],
            text=f"✅ Merci ! Votre don de {amount:,.0f} {currency} a bien été confirmé. 🙏",
        )
    except Exception:
        pass  # l'utilisateur a peut-être bloqué le bot ou jamais démarré de chat privé
