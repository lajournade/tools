#!/bin/bash

echo "✅ Mise à jour des dépôts..."
sudo apt update

# --- apt packages ---
echo "📦 Installation des paquets APT..."
xargs -a $(dirname $0)/apt_apps.txt sudo apt install -y

# --- Discord ---
if ! command -v discord &> /dev/null; then
	echo "🎮 Installation de Discord (paquet .deb)..."
	wget -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"
	sudo apt install -y ./discord.deb
	rm discord.deb
fi

# --- Bitwarden ---
if ! command -v bitwarden &> /dev/null; then
	echo "🔐 Installation de Bitwarden (paquet .deb)..."
	wget -O bitwarden.deb "https://bitwarden.com/download/?app=desktop&platform=linux&variant=deb"
	sudo apt install -y ./bitwarden.deb
	rm bitwarden.deb
fi

# --- Fastfetch ---
if ! command -v fastfetch &> /dev/null; then
	echo "📦 Installation de Fastfetch..."
	add-apt-repository ppa:zhangsongcui3371/fastfetch
	sudo apt update
	sudo apt install fastfetch
fi

# --- oh my posh ---
if ! command -v oh-my-posh &> /dev/null; then
	echo "📦 Installation de oh-my-posh..."
	mkdir -p ~/.local/bin
	curl -s https://ohmyposh.dev/install.sh | bash -s -- -d ~/.local/bin
fi

# --- Nerdy font ---
if [[ ! -f .local/share/fonts/SymbolsNerdFont-Regular.ttf ]]; then
	echo "📝 Installation de Nerdy font..."
	mkdir -p ~/.local/share/fonts
	cd ~/.local/share/fonts
	wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/NerdFontsSymbolsOnly.zip
	unzip NerdFontsSymbolsOnly.zip
	rm NerdFontsSymbolsOnly.zip
fi

echo "✅ Installation terminée."

