# SportyWeatherDisplay
A E-ink Weather and Strava Dashboard

Displays weather forecasts and your recent Strava activities on an e-ink display, perfect for a Raspberry Pi with Waveshare/Inky display.

<img src="images/example1.jpg" width="400" alt="example img">

## Features

- 📊 **Weather Dashboard**: Current conditions, 4-day forecast, moon phase
- 🏃 **Strava Integration**: Recent runs with maps and statistics
- 🖼️ **E-ink Optimized**: High-contrast rendering with pixel-perfect icons
- 🐍 **Native Deployment**: Lightweight Python venv deployment 
- ⏰ **Automated**: Runs on schedule via systemd timer

## Quick Start

### Local Development

1. **Set up configuration:**
   ```bash
   cp settings.example.json settings.json
   # Edit settings.json with your API keys
   ```

2. **Run locally (test mode, preview image only):**
   ```bash
   ./run.sh
   ```

   This will create a virtual environment, install dev dependencies (without e-ink drivers), and generate `eink_display_preview.png`.

### Raspberry Pi (Production)

**Run once manually:**
```bash
./run-pi.sh  # Installs deps and pushes to e-ink display
```

**Deployment:**

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Start:**

1. **On your Raspberry Pi:**
   ```bash
   # Clone the repository
   git clone https://github.com/radioburst/SportyWeatherDisplay.git
   cd SportyWeatherDisplay
   
   # Configure your settings
   cp settings.example.json settings.json
   nano settings.json
   
   # Deploy
   chmod +x deploy/deploy.sh
   ./deploy/deploy.sh
   ```

2. **Done!** Your dashboard will update automatically every 15 minutes.

## Project Structure

```
SportyWeatherDisplay/
├── src/                    # Python source code
│   ├── *.py
│   └── templates/         # HTML/CSS templates
├── icons/                  # Weather icons
├── deploy/                 # Deployment files
├── requirements.txt        # Python dependencies
├── settings.json          # Your configuration
└── run.sh                 # Local run script
```

## Configuration

Edit `settings.json`:
- **OpenWeather API**: Get key from [openweathermap.org](https://openweathermap.org/api)
- **Strava API**: Create app at [strava.com/settings/api](https://www.strava.com/settings/api)
- **Location**: Latitude/longitude for weather

## License

See [LICENSE](LICENSE)
