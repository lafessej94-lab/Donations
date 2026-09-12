"""
Configuration centrale du bot de dons.
Toutes les valeurs sensibles se chargent depuis les variables d'environnement
(fichier .env) - ne jamais coder les clés en dur dans le code.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")          # reçoit les alertes admin
ANNOUNCE_CHAT_ID = os.getenv("ANNOUNCE_CHAT_ID", "")     # groupe/chaîne où on annonce les dons

# --- CinetPay (MTN Money, Airtel Money, Moov Money, Wave) ---
CINETPAY_API_KEY = os.getenv("CINETPAY_API_KEY", "")
CINETPAY_SITE_ID = os.getenv("CINETPAY_SITE_ID", "")
CINETPAY_SECRET = os.getenv("CINETPAY_SECRET", "")       # pour vérifier les notifications
CINETPAY_CURRENCY = os.getenv("CINETPAY_CURRENCY", "XAF")  # XAF pour le Congo-B

# --- PayPal ---
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")         # "sandbox" ou "live"

# --- NOWPayments (crypto) ---
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")

# --- Webhook public (URL exposée par ex. via ngrok ou un VPS) ---
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

# --- Objectif de dons par défaut ---
DEFAULT_GOAL_AMOUNT = float(os.getenv("DEFAULT_GOAL_AMOUNT", "500000"))  # en XAF

# --- Base de données ---
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "donbot.sqlite3"))
