#!/bin/bash
# Run the SportyWeatherDisplay locally

set -e

# Check if settings.json exists
if [ ! -f "settings.json" ]; then
    echo "❌ Error: settings.json not found"
    echo "Please copy settings.example.json to settings.json and configure it"
    exit 1
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
pip install -q --upgrade pip
pip install -q -r requirements-dev.txt

# Run the application with TEST_MODE enabled
echo "🚀 Running SportyWeatherDisplay (test mode)..."
export TEST_MODE=true
python src/main.py

echo "✅ Done! Check eink_display_preview.png"
