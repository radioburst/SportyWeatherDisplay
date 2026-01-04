#!/bin/bash
# Run the SportyWeatherDisplay locally

set -e

# Check if settings.json exists
if [ ! -f "settings.json" ]; then
    echo "❌ Error: settings.json not found"
    echo "Please copy settings.example.json to settings.json and configure it"
    exit 1
fi

# Install system dependencies on Raspberry Pi
if [ -f /etc/rpi-issue ]; then
    echo "🔧 Checking system dependencies..."
    REQUIRED_PKGS="libopenjp2-7 libtiff6 libwebp7 chromium chromium-driver"
    INSTALL_NEEDED=false
    
    for pkg in $REQUIRED_PKGS; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            INSTALL_NEEDED=true
            break
        fi
    done
    
    if [ "$INSTALL_NEEDED" = true ]; then
        echo "Installing required system packages..."
        sudo apt update
        sudo apt install -y $REQUIRED_PKGS
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies (dev version without RPi deps)
echo "📥 Installing dependencies..."
# Use --no-cache-dir and a custom TMPDIR to avoid "No space left on device" on Pi Zero
mkdir -p .pip_tmp
export TMPDIR=$PWD/.pip_tmp
pip install --no-cache-dir -q --upgrade pip
pip install --no-cache-dir -q -r requirements-dev.txt
rm -rf .pip_tmp

# Run the application with TEST_MODE enabled
echo "🚀 Running SportyWeatherDisplay (test mode)..."
export TEST_MODE=true
python src/main.py

echo "✅ Done! Check eink_display_preview.png"
