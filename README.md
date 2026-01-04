# SportyWeatherDisplay
A E-ink Weather and Strava Dashboard

Displays weather forecasts and your recent Strava activities on an e-ink display, perfect for a Raspberry Pi with Waveshare/Inky display.

## Features

- 📊 **Weather Dashboard**: Current conditions, 5-day forecast, moon phase
- 🏃 **Strava Integration**: Recent runs with maps and statistics
- 🖼️ **E-ink Optimized**: Black and white rendering perfect for e-paper displays
- 🐳 **Containerized**: Easy deployment with Podman
- ⏰ **Automated**: Runs on schedule via systemd timer

## Quick Start

### Local Development

1. **Set up configuration:**
   ```bash
   cp settings.example.json settings.json
   # Edit settings.json with your API keys
   ```

2. **Run locally:**
   ```bash
   ./run.sh
   ```

   This will create a virtual environment, install dependencies, and generate `eink_display_preview.png`.

### Raspberry Pi Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions using Podman and systemd.

Quick deploy:
```bash
export RPI_HOST=raspberrypi.local
./deploy/deploy.sh
```

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
