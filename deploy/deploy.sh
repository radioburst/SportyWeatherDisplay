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

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}❌ Error: podman not found${NC}"
    echo "Install podman with: sudo apt install -y podman"
    exit 1
fi

# Build the container image
echo -e "${YELLOW}📦 Building container image...${NC}"
podman build -t ${PROJECT_NAME}:latest -f deploy/Containerfile .

# Create config directory
echo -e "${YELLOW}📁 Setting up configuration...${NC}"
mkdir -p ~/.config/sporty-weather/output

# Copy settings.json
cp settings.json ~/.config/sporty-weather/

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

# Enable lingering to allow user services to run without login
loginctl enable-linger $USER

echo -e "${GREEN}✨ Deployment successful!${NC}"
echo ""
echo "The dashboard will update every 15 minutes automatically."
echo ""
echo "Useful commands:"
echo "  - Check timer status:     systemctl --user status sporty-weather.timer"
echo "  - Check service status:   systemctl --user status sporty-weather.service"
echo "  - View logs:              journalctl --user -u sporty-weather.service -f"
echo "  - Run manually now:       systemctl --user start sporty-weather.service"
echo "  - Stop automatic updates: systemctl --user stop sporty-weather.timer"
echo ""
echo "Output images will be in: ~/.config/sporty-weather/output/"
