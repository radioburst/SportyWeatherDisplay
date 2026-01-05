#!/bin/bash
# Deployment script for Sporty Weather Display on Raspberry Pi
# Run this script ON the Raspberry Pi after cloning the repo

set -e

echo "🚀 Deploying Sporty Weather Display to Raspberry Pi"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_NAME="sporty-weather-display"

# Get the project root directory (parent of deploy/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if settings.json exists
if [ ! -f "settings.json" ]; then
    echo -e "${RED}❌ Error: settings.json not found${NC}"
    echo "Please copy settings.example.json to settings.json and configure it"
    exit 1
fi

echo -e "${YELLOW}📦 Installing python3-venv and system dependencies...${NC}"
sudo apt update
# Use 'chromium' instead of 'chromium-browser' for Debian/Trixie
# Use 'libopenblas-dev' as an alternative to 'libatlas-base-dev'
# We install python3-numpy and python3-pil via apt to avoid long compilation on Pi Zero
sudo apt install -y python3-venv python3-pip python3-dev build-essential \
    chromium libopenjp2-7 libtiff-dev libopenblas-dev fontconfig \
    python3-numpy python3-pil python3-requests python3-jinja2 \
    python3-rpi.gpio python3-spidev xvfb libnss3

# Enable persistent logging if not already enabled
if [ ! -d "/var/log/journal" ]; then
    echo -e "${YELLOW}📝 Enabling persistent systemd journal...${NC}"
    sudo mkdir -p /var/log/journal
    sudo systemd-tmpfiles --create --prefix /var/log/journal
    sudo systemctl restart systemd-journald
fi

# Enable lingering to allow user services to run without login
loginctl enable-linger $USER

# Create virtual environment with system site packages
# This allows using the pre-compiled numpy and pillow from apt
echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
fi

# Install python dependencies
echo -e "${YELLOW}📥 Installing python dependencies...${NC}"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Create config directory
echo -e "${YELLOW}📁 Setting up configuration...${NC}"
mkdir -p ~/.config/sporty-weather/output

# Copy settings.json
cp settings.json ~/.config/sporty-weather/

# Update systemd service with absolute paths
echo -e "${YELLOW}🔧 Configuring systemd service...${NC}"
sed -i "s|ExecStart=.*|ExecStart=$PROJECT_ROOT/venv/bin/python $PROJECT_ROOT/src/main.py|g" deploy/sporty-weather.service
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_ROOT|g" deploy/sporty-weather.service

# Install systemd service files
echo -e "${YELLOW}🔧 Installing systemd services...${NC}"
mkdir -p ~/.config/systemd/user/
cp deploy/sporty-weather.service ~/.config/systemd/user/
cp deploy/sporty-weather.timer ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable and start the timer
echo -e "${YELLOW}⏰ Enabling systemd timer...${NC}"
systemctl --user enable sporty-weather.timer
systemctl --user start sporty-weather.timer

# Trigger a manual run immediately so we can see logs
echo -e "${YELLOW}🏃 Triggering initial run...${NC}"
systemctl --user start sporty-weather.service

echo -e "${GREEN}✨ Deployment successful!${NC}"
echo "The dashboard will update every 15 minutes automatically."
echo ""
echo "Useful commands:"
echo "  - View logs (NOW):         journalctl --user -u sporty-weather.service -f"
echo "  - Check timer status:      systemctl --user status sporty-weather.timer"
echo "  - Run manually again:      systemctl --user start sporty-weather.service"
echo "  - Stop automatic updates: systemctl --user stop sporty-weather.timer"
echo ""
echo "Output images will be in: ~/.config/sporty-weather/output/"
