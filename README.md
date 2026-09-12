# Bot de dons Telegram

Bot Telegram permettant de recevoir des dons via **MTN Money, Airtel Money, Moov Money,
Wave** (via CinetPay), **PayPal** et **crypto-monnaie** (via NOWPayments), avec
classement des donateurs, barre de progression d'objectif et notifications automatiques.

## ⚠️ Important à savoir avant de commencer

Le mobile money (MTN, Airtel, Moov, Wave) ne peut pas être branché directement à un
bot : ces opérateurs ne fournissent pas d'API publique à un particulier. Il faut passer
par un **agrégateur de paiement** qui a des accords marchands avec eux. Ce projet utilise
**CinetPay**, très répandu en Afrique centrale et de l'Ouest (y compris au Congo), qui
couvre les 4 opérateurs avec un seul compte. Vous devrez :

1. Créer un compte marchand sur [cinetpay.com](https://cinetpay.com)
2. Passer la vérification KYC (pièce d'identité, infos sur l'activité)
3. Récupérer votre `APIKEY` et `SITE_ID` dans le tableau de bord

De même, PayPal et NOWPayments nécessitent chacun leur propre compte développeur/marchand.

## Architecture

```
donbot/
├── bot.py              # Bot Telegram (commandes, flux de don)
├── webhook_server.py   # Serveur FastAPI qui reçoit les confirmations de paiement
├── notifier.py         # Envoie les notifications Telegram après un don confirmé
├── database.py         # Base SQLite (dons, objectif, classement)
├── config.py            # Chargement de la config depuis .env
├── payments/
│   ├── cinetpay.py     # MTN / Airtel / Moov / Wave
│   ├── paypal.py       # PayPal
│   └── crypto.py       # Crypto via NOWPayments
├── requirements.txt
└── .env.example
```

## Installation

```bash
cd donbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Remplissez `.env` avec vos vraies clés (voir section suivante).

### 1. Créer le bot Telegram
- Parlez à [@BotFather](https://t.me/BotFather) sur Telegram
- `/newbot` → suivez les instructions → copiez le token dans `TELEGRAM_BOT_TOKEN`
- `ADMIN_CHAT_ID` : votre propre chat_id (utilisez [@userinfobot](https://t.me/userinfobot))
- `ANNOUNCE_CHAT_ID` : l'id du groupe/canal où annoncer publiquement les dons

### 2. CinetPay (mobile money)
- Créez un compte sur cinetpay.com, activez le mode "Checkout"
- Renseignez `CINETPAY_API_KEY`, `CINETPAY_SITE_ID`, `CINETPAY_SECRET`

### 3. PayPal
- Créez une app sur [developer.paypal.com](https://developer.paypal.com)
- Renseignez `PAYPAL_CLIENT_ID` et `PAYPAL_SECRET`
- Laissez `PAYPAL_MODE=sandbox` pour tester, passez à `live` en production

### 4. NOWPayments (crypto)
- Créez un compte sur [nowpayments.io](https://nowpayments.io)
- Récupérez votre clé API et votre secret IPN dans les paramètres

### 5. Exposer le webhook publiquement
Les fournisseurs de paiement doivent pouvoir appeler votre serveur. En développement,
utilisez [ngrok](https://ngrok.com) :

```bash
ngrok http 8000
```

Copiez l'URL https générée (ex: `https://abcd1234.ngrok-free.app`) dans `PUBLIC_BASE_URL`.
En production, déployez sur un VPS avec un vrai nom de domaine + HTTPS (Let's Encrypt).

## Lancer le bot

Deux processus à faire tourner en parallèle :

```bash
# Terminal 1 : le serveur qui reçoit les confirmations de paiement
uvicorn webhook_server:app --host 0.0.0.0 --port 8000

# Terminal 2 : le bot Telegram
python bot.py
```

## Utilisation

| Commande       | Description                                  |
|----------------|-----------------------------------------------|
| `/start`       | Message de bienvenue                          |
| `/don`         | Lance le flux de don (méthode → montant → lien)|
| `/classement`  | Top 10 des donateurs                          |
| `/objectif`    | Progression vers l'objectif de collecte       |
| `/aide`        | Aide                                           |

Le montant de l'objectif se change directement en base via `database.set_goal(montant)`,
ou vous pouvez ajouter une commande admin `/objectif_set` si besoin.

## Sécurité

- Les webhooks CinetPay sont revérifiés côté serveur (`/payment/check`) avant de valider
  un don — on ne fait jamais confiance aveuglément à la notification reçue.
- Les webhooks NOWPayments sont vérifiés par signature HMAC-SHA512.
- Ne committez jamais votre fichier `.env` dans un dépôt public.

## Limites connues / à améliorer

- Pas de gestion multi-devises automatique (taux de change) entre XAF et USD.
- Pas d'interface admin web pour changer l'objectif ou voir l'historique — tout passe
  par la base SQLite ou des commandes Telegram à ajouter.
- Pour un usage à fort volume, remplacer SQLite par PostgreSQL.
