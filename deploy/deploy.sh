#!/bin/bash
# Deployment script for Sporty Weather Display on Raspberry Pi

set -e

echo "🚀 Deploying Sporty Weather Display to Raspberry Pi"
echo "=================================================="

# Configuration
RPI_USER="${RPI_USER:-pi}"
RPI_HOST="${RPI_HOST:-raspberrypi.local}"
PROJECT_NAME="sporty-weather-display"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if settings.json exists
if [ ! -f "settings.json" ]; then
    echo -e "${RED}❌ Error: settings.json not found${NC}"
    echo "Please copy settings.example.json to settings.json and configure it"
    exit 1
fi

# Build the container
echo -e "${YELLOW}📦 Building container image...${NC}"
podman build -t ${PROJECT_NAME}:latest -f deploy/Containerfile .

# Save the container image to a tar file
echo -e "${YELLOW}💾 Saving container image...${NC}"
podman save -o ${PROJECT_NAME}.tar localhost/${PROJECT_NAME}:latest

# Copy files to Raspberry Pi
echo -e "${YELLOW}📤 Copying files to Raspberry Pi...${NC}"
ssh ${RPI_USER}@${RPI_HOST} "mkdir -p ~/.config/sporty-weather"
scp settings.json ${RPI_USER}@${RPI_HOST}:~/.config/sporty-weather/
scp ${PROJECT_NAME}.tar ${RPI_USER}@${RPI_HOST}:/tmp/
scp deploy/sporty-weather.service ${RPI_USER}@${RPI_HOST}:/tmp/
scp deploy/sporty-weather.timer ${RPI_USER}@${RPI_HOST}:/tmp/

# Deploy on Raspberry Pi
echo -e "${YELLOW}🔧 Setting up on Raspberry Pi...${NC}"
ssh ${RPI_USER}@${RPI_HOST} << 'ENDSSH'
    set -e
    
    # Load the container image
    echo "Loading container image..."
    podman load -i /tmp/sporty-weather-display.tar
    
    # Create output directory
    mkdir -p ~/.config/sporty-weather/output
    
    # Install systemd service files
    mkdir -p ~/.config/systemd/user/
    mv /tmp/sporty-weather.service ~/.config/systemd/user/
    mv /tmp/sporty-weather.timer ~/.config/systemd/user/
    
    # Reload systemd
    systemctl --user daemon-reload
    
    # Enable and start the timer
    systemctl --user enable sporty-weather.timer
    systemctl --user start sporty-weather.timer
    
    # Enable lingering to allow user services to run without login
    loginctl enable-linger $USER
    
    # Clean up
    rm /tmp/sporty-weather-display.tar
    
    echo "✅ Deployment complete!"
    echo "Timer status:"
    systemctl --user status sporty-weather.timer --no-pager
ENDSSH

# Clean up local tar file
rm ${PROJECT_NAME}.tar

echo -e "${GREEN}✨ Deployment successful!${NC}"
echo ""
echo "Useful commands on the Raspberry Pi:"
echo "  - Check timer status:     systemctl --user status sporty-weather.timer"
echo "  - Check service status:   systemctl --user status sporty-weather.service"
echo "  - View logs:              journalctl --user -u sporty-weather.service -f"
echo "  - Run manually:           systemctl --user start sporty-weather.service"
echo "  - Stop timer:             systemctl --user stop sporty-weather.timer"
