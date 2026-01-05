# Deployment Guide for Raspberry Pi

This guide covers deploying the Sporty Weather Display to a Raspberry Pi using a native Python virtual environment and systemd.

## Architecture

The deployment uses:
- **Python Virtual Environment**: Isolates dependencies 
- **systemd user service**: Manages the application lifecycle
- **systemd timer**: Schedules automatic updates (every 15 minutes)

## Prerequisites

### On your Raspberry Pi:
```bash
# Install git
sudo apt update
sudo apt install -y git

# Ensure SPI is enabled for e-ink display
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
# Reboot when prompted
```

**Important:** You must disable SPI's chip-select in `/boot/firmware/config.txt`:

```bash
echo "dtoverlay=spi0-0cs" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

**Note:** The deployment script will check these prerequisites and install all necessary system libraries (Chromium, fontconfig, etc.) automatically.

## Deployment

### 1. Clone the Repository on Your Raspberry Pi

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Clone the repository
cd ~
git clone https://github.com/radioburst/SportyWeatherDisplay.git
cd SportyWeatherDisplay
```

### 2. Configure Settings

```bash
# Copy the example settings
cp settings.example.json settings.json

# Edit with your API keys
nano settings.json
```

Add your:
- OpenWeather API key (get from [openweathermap.org/api](https://openweathermap.org/api))
- Strava API credentials (create app at [strava.com/settings/api](https://www.strava.com/settings/api))
- Location details (latitude/longitude)

### 3. Run the Deployment Script

```bash
# Make the script executable
chmod +x deploy/deploy.sh

# Run the deployment
./deploy/deploy.sh
```

That's it! The script will:
1. Install system dependencies (Chromium, fontconfig, etc.)
2. Create a Python virtual environment and install requirements
3. Set up systemd service and timer
4. Start automatic updates every 15 minutes
5. Enable lingering so it runs even when you're not logged in

### Management Commands

```bash
# Check timer status
systemctl --user list-timers | grep sporty

# Check service status
systemctl --user status sporty-weather.service

# View logs
journalctl --user -u sporty-weather.service -f

# Run manually once
systemctl --user start sporty-weather.service

# Check timer status
systemctl --user status sporty-weather.timer

# Check last run
systemctl --user status sporty-weather.service

# View logs
journalctl --user -u sporty-weather.service -f

# Run immediately (manual trigger)
systemctl --user start sporty-weather.service

# Stop automatic updates
systemctl --user stop sporty-weather.timer

# Restart timer
systemctl --user restart sporty-weather.timer

# List all runs
journalctl --user -u sporty-weather.service --since today
```

## Customization

### Configuration

After deployment, the active configuration file is moved to your user's config directory. If you want to change your API keys or settings, edit this file:

```bash
nano ~/.config/sporty-weather/settings.json
```

The service will pick up the changes on the next scheduled run.

### Change Update Frequency

Edit `sporty-weather.timer` and modify the `OnCalendar` line:
- Every 15 minutes: `OnCalendar=*:0/15`
- Every 30 minutes: `OnCalendar=*:0/30`
- Every hour: `OnCalendar=hourly`
- Specific times: `OnCalendar=08:00,12:00,18:00`

After changes, reload systemd:
```bash
systemctl --user daemon-reload
systemctl --user restart sporty-weather.timer
```
