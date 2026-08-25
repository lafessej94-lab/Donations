# Donations

# Bot de dons

Bot Telegram indépendant pour recevoir des dons (Airtel Money, Mobile Money, Crypto)
et financer le bot anime/hardsub. Validation semi-manuelle par un admin (ton collègue).

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# remplis .env avec tes vraies infos (API Telegram, numéros, wallets, ID admin)
python bot.py
```

## Obtenir API_ID / API_HASH
Va sur https://my.telegram.org → API development tools → crée une app.

## Obtenir BOT_TOKEN
Parle à [@BotFather](https://t.me/BotFather) sur Telegram → `/newbot`.

## Obtenir ton ADMIN_ID (celui de ton collègue)
Demande-lui de parler à [@userinfobot](https://t.me/userinfobot), il obtiendra son ID Telegram.

## Fonctionnement

1. `/don` → l'utilisateur choisit Airtel Money / Mobile Money / Crypto
2. Le bot affiche le numéro ou l'adresse wallet correspondant
3. L'utilisateur clique "J'ai payé" puis envoie une capture d'écran
4. L'admin reçoit la preuve avec boutons **Confirmer** / **Rejeter**
5. Si confirmé → l'utilisateur reçoit un message de remerciement automatique

## Commandes admin
- `/dons_stats` : voir le nombre de dons confirmés par méthode + les dons en attente

## Évolution possible (V2)
- Brancher une API de vérification automatique pour la crypto (ex: NowPayments)
  pour supprimer l'étape manuelle sur cette méthode
- Brancher un agrégateur (CinetPay, PawaPay) si un compte marchand Airtel/Mobile Money
  est disponible, pour automatiser complètement la confirmation
