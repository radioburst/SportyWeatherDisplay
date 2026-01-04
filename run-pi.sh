#!/bin/bash
# Run the SportyWeatherDisplay on Raspberry Pi (production mode with e-ink display)

set -e

# Check if settings.json exists
if [ ! -f "settings.json" ]; then
    echo "❌ Error: settings.json not found"
    echo "Please copy settings.example.json to settings.json and configure it"
    exit 1
fi

# Install system dependencies on Raspberry Pi
echo "🔧 Checking system dependencies..."
REQUIRED_PKGS="libopenjp2-7 libtiff6 libwebp7 chromium chromium-driver libopenblas0"
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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment and installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Use --no-cache-dir and a custom TMPDIR only during initial setup
    mkdir -p .pip_tmp
    export TMPDIR=$PWD/.pip_tmp
    pip install --no-cache-dir -q --upgrade pip
    pip install --no-cache-dir -q -r requirements.txt
    rm -rf .pip_tmp
else
    # Just activate it if it already exists
    source venv/bin/activate
fi

# Run the application in production mode (will push to e-ink display)
echo "🚀 Running SportyWeatherDisplay (production mode)..."
export TEST_MODE=false
python src/main.py

echo "✅ Done! Dashboard pushed to e-ink display."
