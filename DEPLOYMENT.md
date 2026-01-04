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
# Install Podman
sudo apt update
sudo apt install -y podman

# Ensure SPI is enabled for e-ink display
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
```

### On your development machine:
- Podman installed
- SSH access to your Raspberry Pi
- `settings.json` configured with your API keys

## Configuration

1. Copy the example settings file:
```bash
cp settings.example.json settings.json
```

2. Edit `settings.json` with your credentials:
   - OpenWeather API key
   - Strava API credentials
   - Location details

## Deployment

### Automated Deployment

Use the provided deployment script:

```bash
# Set your Raspberry Pi details (or use defaults)
export RPI_USER=pi
export RPI_HOST=raspberrypi.local

# Run the deployment script
./deploy.sh
```

This script will:
1. Build the container image locally
2. Transfer it to your Raspberry Pi
3. Set up systemd service and timer
4. Start the automatic updates

### Manual Deployment

If you prefer to deploy manually:

#### 1. Build the container
```bash
podman build -t sporty-weather-display:latest -f deploy/Containerfile .
```

#### 2. Transfer to Raspberry Pi
```bash
# Save and transfer the image
podman save -o sporty-weather-display.tar localhost/sporty-weather-display:latest
scp sporty-weather-display.tar pi@raspberrypi.local:/tmp/

# Load on the Raspberry Pi
ssh pi@raspberrypi.local
podman load -i /tmp/sporty-weather-display.tar
```

#### 3. Set up configuration on Raspberry Pi
```bash
# Create config directory
mkdir -p ~/.config/sporty-weather

# Copy settings.json (from your dev machine)
scp settings.json pi@raspberrypi.local:~/.config/sporty-weather/
```

#### 4. Install systemd services
```bash
# Copy service files to Raspberry Pi
scp sporty-weather.service sporty-weather.timer pi@raspberrypi.local:/tmp/

# On the Raspberry Pi, install them
ssh pi@raspberrypi.local
mkdir -p ~/.config/systemd/user/
mv /tmp/sporty-weather.* ~/.config/systemd/user/

# Reload systemd and enable services
systemctl --user daemon-reload
systemctl --user enable sporty-weather.timer
systemctl --user start sporty-weather.timer

# Enable lingering (allows services to run without being logged in)
loginctl enable-linger $USER
```

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

To deploy new code:
1. Make your changes locally
2. Run `./deploy.sh` again
3. The new container will be used on the next scheduled run

## Troubleshooting

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
