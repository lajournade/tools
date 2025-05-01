#!/bin/bash

echo "✅ Mise à jour des dépôts..."
sudo apt update

echo "📦 Installation des paquets APT..."
xargs -a apt_apps.txt sudo apt install -y

# --- DISCORD --
if ! command -v discord &> /dev/null; then
	echo "🎮 Installation de Discord (paquet .deb)..."
	wget -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"
	sudo apt install -y ./discord.deb
	rm discord.deb
fi

# --- BITWARDEN --
if ! command -v bitwarden &> /dev/null; then
	echo "🔐 Installation de Bitwarden (paquet .deb)..."
	wget -O bitwarden.deb "https://bitwarden.com/download/?app=desktop&platform=linux&variant=deb"
	sudo apt install -y ./bitwarden.deb
	rm bitwarden.deb
fi

echo "✅ Installation terminée."

