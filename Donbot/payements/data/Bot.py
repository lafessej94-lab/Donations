"""
Bot Telegram de dons.

Commandes :
  /start       - message de bienvenue
  /don         - lance le flux de don (choix méthode -> montant -> lien de paiement)
  /classement  - top 10 des donateurs
  /objectif    - progression vers l'objectif de collecte
  /aide        - aide

Lancer avec : python bot.py
(le serveur webhook_server.py doit tourner en parallèle pour recevoir les confirmations)
"""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters,
)

import database as db
from config import TELEGRAM_BOT_TOKEN, CINETPAY_CURRENCY
from payments import cinetpay, paypal, crypto
from notifier import format_progress_bar

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

CHOOSING_METHOD, ENTERING_AMOUNT = range(2)

METHOD_LABELS = {
    "mtn": "🟡 MTN Money",
    "airtel": "🔴 Airtel Money",
    "moov": "🔵 Moov Money",
    "wave": "🌊 Wave",
    "paypal": "💳 PayPal",
    "crypto": "₿ Crypto",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue ! Ce bot permet de faire un don en toute simplicité.\n\n"
        "/don — faire un don\n"
        "/classement — voir les meilleurs donateurs\n"
        "/objectif — voir la progression de la collecte\n"
        "/aide — aide"
    )


async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Comment faire un don ?*\n"
        "1. Tapez /don\n"
        "2. Choisissez votre moyen de paiement (MTN, Airtel, Moov, Wave, PayPal, crypto)\n"
        "3. Indiquez le montant\n"
        "4. Suivez le lien de paiement reçu\n"
        "5. Vous recevrez une confirmation automatique une fois le paiement validé.",
        parse_mode="Markdown",
    )


# ---------- Flux /don ----------

async def don_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in METHOD_LABELS.items()
    ]
    await update.message.reply_text(
        "Choisissez votre moyen de paiement :",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_METHOD


async def method_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["method"] = query.data
    await query.edit_message_text(
        f"Moyen choisi : {METHOD_LABELS[query.data]}\n\n"
        f"Indiquez le montant à donner "
        f"({'en XAF' if query.data in ('mtn','airtel','moov','wave') else 'en USD'}) :"
    )
    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Montant invalide. Entrez un nombre, ex: 5000")
        return ENTERING_AMOUNT

    method = context.user_data["method"]
    user = update.effective_user
    currency = CINETPAY_CURRENCY if method in ("mtn", "airtel", "moov", "wave") else "USD"

    donation_id = db.create_pending_donation(
        telegram_user_id=user.id,
        username=user.username or user.first_name,
        amount=amount,
        currency=currency,
        method=method,
    )

    await update.message.reply_text("⏳ Génération du lien de paiement...")

    if method in ("mtn", "airtel", "moov", "wave"):
        result = cinetpay.create_payment(
            amount=amount,
            description=f"Don Telegram #{donation_id}",
            donation_id=donation_id,
            customer_name=user.first_name or "Donateur",
        )
        if result["ok"]:
            db.set_provider_ref(donation_id, result["transaction_id"])
            await update.message.reply_text(
                f"✅ Cliquez ici pour payer via {METHOD_LABELS[method]} :\n{result['payment_url']}"
            )
        else:
            await update.message.reply_text(f"❌ Erreur : {result['error']}")

    elif method == "paypal":
        result = paypal.create_order(amount, donation_id)
        if result["ok"]:
            db.set_provider_ref(donation_id, result["order_id"])
            await update.message.reply_text(f"✅ Payez via PayPal :\n{result['approve_url']}")
        else:
            await update.message.reply_text(f"❌ Erreur PayPal : {result['error']}")

    elif method == "crypto":
        result = crypto.create_invoice(amount, donation_id)
        if result["ok"]:
            db.set_provider_ref(donation_id, str(result["invoice_id"]))
            await update.message.reply_text(f"✅ Payez en crypto ici :\n{result['payment_url']}")
        else:
            await update.message.reply_text(f"❌ Erreur crypto : {result['error']}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Don annulé.")
    return ConversationHandler.END


# ---------- Classement & objectif ----------

async def classement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = db.get_leaderboard(10)
    if not top:
        await update.message.reply_text("Aucun don confirmé pour le moment.")
        return
    lines = ["🏆 *Classement des donateurs*\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["username"] or f"Utilisateur {row['telegram_user_id']}"
        lines.append(f"{medal} {name} — {row['total']:,.0f}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def objectif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal = db.get_goal()
    total = db.get_total_paid()
    bar = format_progress_bar(total, goal["target_amount"])
    await update.message.reply_text(
        f"🎯 *Objectif de collecte*\n"
        f"{total:,.0f} / {goal['target_amount']:,.0f} {goal['currency']}\n"
        f"{bar}",
        parse_mode="Markdown",
    )


def main():
    db.init_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    don_conv = ConversationHandler(
        entry_points=[CommandHandler("don", don_start)],
        states={
            CHOOSING_METHOD: [CallbackQueryHandler(method_chosen)],
            ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aide", aide))
    app.add_handler(CommandHandler("classement", classement))
    app.add_handler(CommandHandler("objectif", objectif))
    app.add_handler(don_conv)

    log.info("Bot démarré.")
    app.run_polling()


if __name__ == "__main__":
    main()
