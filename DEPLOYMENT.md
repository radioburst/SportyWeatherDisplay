# Deployment Guide for Raspberry Pi

This guide covers deploying the Sporty Weather Display to a Raspberry Pi using Podman and systemd.

## Architecture

The deployment uses:
- **Podman**: Daemonless container runtime (more lightweight than Docker)
- **systemd user service**: Manages the container lifecycle
- **systemd timer**: Schedules automatic updates (every 15 minutes)

This approach is best practice because:
- Containers isolate all Python dependencies
- systemd provides reliable scheduling and automatic restarts
- User services don't require root privileges
- The container can access the e-ink display via device mounting

## Prerequisites

### On your Raspberry Pi:
```bash
# Install Podman and git
sudo apt update
sudo apt install -y podman git

# Ensure SPI is enabled for e-ink display
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
# Reboot when prompted

# Add your user to spi and gpio groups (for device access)
sudo usermod -a -G spi,gpio $USER

# Log out and back in for group changes to take effect
```

**Note:** The deployment script will check these prerequisites automatically.

## Deployment

### 1. Clone the Repository on Your Raspberry Pi

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Clone the repository
cd ~
git clone https://github.com/YOUR_USERNAME/SportyWeatherDisplay.git
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
1. Build the container image
2. Set up systemd service and timer
3. Start automatic updates every 15 minutes
4. Enable lingering so it runs even when you're not logged in

## Management Commands

### On the Raspberry Pi:

```bash
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

## Testing the Container Locally

Before deploying, you can test the container:

```bash
# Build the image
podman build -t sporty-weather-display:latest -f deploy/Containerfile .

# Run once
podman run --rm \
    -v ./settings.json:/app/settings.json:ro \
    -v ./output:/output:rw \
    sporty-weather-display:latest
```

## Customization

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

### Update the Container

To deploy new code after making changes:

```bash
# On your Raspberry Pi
cd ~/SportyWeatherDisplay

# Pull latest changes
git pull

# Re-run the deployment script
./deploy/deploy.sh
```

The new container will be used on the next scheduled run (or run manually with `systemctl --user start sporty-weather.service`).

## Troubleshooting

### E-ink Display Access

The container accesses the e-ink display through SPI devices:
- `/dev/spidev0.0` - SPI interface
- `/dev/gpiomem` - GPIO memory access

These devices are mounted into the container via the systemd service.

**If the display doesn't update:**

1. **Check SPI is enabled:**
   ```bash
   ls -l /dev/spidev0.0
   # Should show the device exists
   ```

2. **Verify group membership:**
   ```bash
   groups
   # Should include: spi, gpio
   ```
   
   If not, add yourself:
   ```bash
   sudo usermod -a -G spi,gpio $USER
   # Log out and back in
   ```

3. **Test the display works:**
   ```bash
   # Run the service manually to see errors
   systemctl --user start sporty-weather.service
   journalctl --user -u sporty-weather.service -n 50
   ```

### Container doesn't start
```bash
# Check logs
journalctl --user -u sporty-weather.service -n 50

# Test container manually
podman run --rm -v ~/.config/sporty-weather/settings.json:/app/settings.json:ro localhost/sporty-weather-display:latest
```

### Timer not running
```bash
# Check if timer is active
systemctl --user list-timers

# Ensure lingering is enabled
loginctl show-user $USER | grep Linger
```

### Display not updating
```bash
# Check if container has device access
ls -l /dev/spidev0.0 /dev/gpiomem

# Ensure user is in correct groups
groups
# Should include: spi, gpio
```

## Architecture Benefits

This setup provides:
- **Isolation**: Python dependencies contained, won't conflict with system packages
- **Reliability**: systemd automatically restarts on failure
- **Scheduling**: Built-in timer replaces cron
- **Logging**: Centralized logs via journald
- **Security**: Runs as user service, minimal privileges
- **Portability**: Container can run anywhere with Podman
- **Rootless**: No root access needed for daily operation

## File Structure

```
SportyWeatherDisplay/
├── src/                       # Python source code
│   ├── main.py
│   ├── weather.py
│   ├── strava.py
│   ├── get_strava_token.py
│   └── templates/            # HTML/CSS templates
│       ├── dashboard.html
│       └── dashboard.css
├── icons/                     # Weather icons
├── deploy/                    # Deployment files
│   ├── Containerfile          # Container definition
│   ├── sporty-weather.service # systemd service unit
│   ├── sporty-weather.timer   # systemd timer unit
│   ├── deploy.sh             # Automated deployment script
│   └── .containerignore      # Container build exclusions
├── requirements.txt           # Python dependencies
├── settings.json             # API keys & configuration
├── settings.example.json     # Example configuration
├── DEPLOYMENT.md             # This file
├── README.md
└── LICENSE
```
