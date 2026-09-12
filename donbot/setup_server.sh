#!/bin/bash
# Script d'installation du bot de dons sur un serveur Ubuntu/Debian.
# Usage : bash setup_server.sh

set -e

echo "==> Mise à jour du système"
sudo apt update && sudo apt upgrade -y

echo "==> Installation de Python, pip, venv, git, et certbot (HTTPS)"
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

echo "==> Clonage du dépôt"
read -p "URL du dépôt Git (ex: https://github.com/lafessej94-lab/Donations.git) : " REPO_URL
git clone "$REPO_URL" donbot
cd donbot

echo "==> Création de l'environnement virtuel"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Configuration du fichier .env"
cp .env.example .env
echo "⚠️  Éditez maintenant le fichier .env avec vos vraies clés :"
echo "    nano donbot/.env"
echo ""
echo "Une fois fait, relancez ce script ou passez à l'étape suivante manuellement."
