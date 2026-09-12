# Déployer et tester le bot sur un serveur (VPS)

Ce guide suppose un serveur Ubuntu/Debian tout neuf (DigitalOcean, OVH, Contabo,
Hetzner, AWS Lightsail... n'importe lequel avec un accès SSH root ou sudo).

## 1. Se connecter au serveur

```bash
ssh utilisateur@ip.du.serveur
```

## 2. Installer et cloner le projet

Copiez `setup_server.sh` sur le serveur (ou clonez directement votre dépôt une
fois qu'il contient bien tous les fichiers), puis :

```bash
chmod +x setup_server.sh
./setup_server.sh
```

Ce script installe Python, Nginx, Certbot, clone votre dépôt, crée l'environnement
virtuel et installe les dépendances.

## 3. Configurer le fichier .env

```bash
cd donbot
nano .env
```

Remplissez au minimum `TELEGRAM_BOT_TOKEN`. Pour un premier test rapide, vous
pouvez laisser les clés de paiement vides — le bot démarrera quand même, seules
les commandes `/don` avec paiement échoueront tant que les clés ne sont pas
renseignées.

Mettez aussi `PUBLIC_BASE_URL=https://votre-domaine.com` (voir étape 5).

## 4. Premier test manuel (sans systemd)

Avant d'automatiser, testez à la main pour repérer les erreurs facilement :

```bash
source venv/bin/activate
python bot.py
```

Ouvrez Telegram, cherchez votre bot, envoyez `/start`. S'il répond, tout va bien.
Arrêtez avec `Ctrl+C`.

Dans un second terminal (ou une seconde session SSH) :

```bash
source venv/bin/activate
uvicorn webhook_server:app --host 0.0.0.0 --port 8000
```

Testez qu'il répond :
```bash
curl http://localhost:8000/thanks
```
Vous devriez voir : `Merci pour votre don ! Retournez sur Telegram...`

## 5. Exposer le webhook publiquement (obligatoire pour les paiements réels)

### Option A — nom de domaine + Nginx + HTTPS (recommandé, production)

1. Pointez un nom de domaine (ou sous-domaine) vers l'IP de votre serveur (enregistrement DNS de type A).
2. Copiez `deploy/nginx_donbot.conf` :
   ```bash
   sudo cp deploy/nginx_donbot.conf /etc/nginx/sites-available/donbot
   sudo nano /etc/nginx/sites-available/donbot   # remplacez "votre-domaine.com"
   sudo ln -s /etc/nginx/sites-available/donbot /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d votre-domaine.com
   ```
3. Mettez à jour `.env` : `PUBLIC_BASE_URL=https://votre-domaine.com`

### Option B — ngrok (rapide, pour tester seulement, pas pour la production)

```bash
sudo snap install ngrok
ngrok http 8000
```
Copiez l'URL `https://xxxx.ngrok-free.app` affichée dans `.env` (`PUBLIC_BASE_URL`).
⚠️ Cette URL change à chaque redémarrage de ngrok (sauf compte payant) — pas
adapté à un usage durable.

## 6. Faire tourner le bot en permanence (systemd)

Une fois les tests manuels concluants, installez les services pour que le bot
redémarre automatiquement (au boot du serveur, ou s'il plante) :

```bash
sudo cp deploy/donbot.service /etc/systemd/system/donbot@.service
sudo cp deploy/donbot-webhook.service /etc/systemd/system/donbot-webhook@.service

sudo systemctl daemon-reload
sudo systemctl enable --now donbot@$(whoami).service
sudo systemctl enable --now donbot-webhook@$(whoami).service
```

Vérifier que tout tourne :
```bash
sudo systemctl status donbot@$(whoami).service
sudo systemctl status donbot-webhook@$(whoami).service
```

Voir les logs en direct (utile pour déboguer) :
```bash
journalctl -u donbot@$(whoami).service -f
journalctl -u donbot-webhook@$(whoami).service -f
```

Redémarrer après une modification du code ou du `.env` :
```bash
sudo systemctl restart donbot@$(whoami).service
sudo systemctl restart donbot-webhook@$(whoami).service
```

## 7. Test de bout en bout

1. Sur Telegram, envoyez `/don` à votre bot.
2. Choisissez un moyen de paiement, entrez un petit montant (ex: 100 XAF ou 1 USD).
3. Cliquez le lien reçu et effectuez un vrai paiement de test.
   - CinetPay et PayPal ont des modes sandbox/test — utilisez-les avant de passer en argent réel.
   - `PAYPAL_MODE=sandbox` dans `.env` pour PayPal.
4. Vérifiez que vous recevez bien la confirmation Telegram automatique.
5. Vérifiez `/classement` et `/objectif` pour voir le don apparaître.

## Dépannage rapide

| Symptôme | Cause probable |
|---|---|
| Le bot ne répond pas du tout sur Telegram | Mauvais `TELEGRAM_BOT_TOKEN`, ou le service n'est pas démarré (`systemctl status`) |
| Lien de paiement jamais généré | Clé API du fournisseur manquante/invalide dans `.env` |
| Paiement effectué mais pas de confirmation Telegram | `PUBLIC_BASE_URL` injoignable depuis l'extérieur (pare-feu, DNS, HTTPS cassé) — testez avec `curl https://votre-domaine.com/thanks` depuis un autre ordinateur |
| Erreur 401 sur le webhook crypto | `NOWPAYMENTS_IPN_SECRET` incorrect |
