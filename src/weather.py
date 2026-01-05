import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import base64
import io
import os
import json

# Path to settings file
def get_settings_path():
    config_path = os.path.expanduser('~/.config/sporty-weather/settings.json')
    if os.path.exists(config_path):
        return config_path
    # Fallback to project root
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

SETTINGS_FILE = get_settings_path()

def load_settings():
    """Load settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    raise FileNotFoundError(f"Settings file not found: {SETTINGS_FILE}")

# Weather icon mapping to OpenWeather codes
WEATHER_ICON_MAP = {
    'Clear': '01d',
    'Clouds': '02d',
    'Rain': '10d',
    'Drizzle': '09d',
    'Thunderstorm': '11d',
    'Snow': '13d',
    'Mist': '50d',
    'Fog': '50d',
    'Haze': '50d'
}

def get_moon_phase(date=None):
    """Calculate moon phase as percentage (0-100) for a given date"""
    if date is None:
        date = datetime.now()
    # Known new moon date (January 11, 2024)
    known_new_moon = datetime(2024, 1, 11)
    days_since = (date - known_new_moon).days
    lunar_cycle = 29.53
    phase = (days_since % lunar_cycle) / lunar_cycle * 100
    return int(phase)

def get_icon_base64(icon_name):
    """Convert icon to base64 data URI"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(project_root, 'icons', f'{icon_name}.png')
    
    # If night icon doesn't exist, try day version
    if not os.path.exists(icon_path) and icon_name.endswith('n'):
        icon_name = icon_name[:-1] + 'd'
        icon_path = os.path.join(project_root, 'icons', f'{icon_name}.png')
    
    if os.path.exists(icon_path):
        with open(icon_path, 'rb') as f:
            img_data = f.read()
            img_str = base64.b64encode(img_data).decode()
            return f"data:image/png;base64,{img_str}"
    return None

from PIL import Image, ImageDraw

def draw_moon_phase(phase, size=24):
    import math
    # Create a crisp RGBA image
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    
    # Use float centers for better symmetry
    center = (size - 1) / 2.0
    radius = (size / 2.0) - 1.0
    
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx*dx + dy*dy)
            
            # 1. Draw the 1-pixel black outline
            if radius <= dist < radius + 1.0:
                pixels[x, y] = (0, 0, 0, 255)
                
            # 2. Draw the moon body
            elif dist < radius:
                # Calculate the horizontal width of the moon at this specific Y
                local_r = math.sqrt(radius*radius - dy*dy)
                
                # The terminator is an ellipse that shifts based on the phase
                # We calculate the x-offset of the terminator line
                term_x = local_r * math.cos(2 * math.pi * phase)
                
                is_lit = False
                if phase <= 0.5: 
                    # Waxing: Lit part is on the right
                    if dx > term_x: is_lit = True
                else: 
                    # Waning: Lit part is on the left
                    # We flip the terminator position for the second half of the cycle
                    if dx < -term_x: is_lit = True
                
                # Flip colors: Lit part is White, Shadow part is Black
                if is_lit:
                    pixels[x, y] = (255, 255, 255, 255) # White (Lit)
                else:
                    pixels[x, y] = (0, 0, 0, 255) # Black (Shadow)

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def draw_raindrop(percent, size=24):
    """Draw a pixel-perfect raindrop filled by percentage"""
    import math
    # Create a crisp RGBA image
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    
    # Raindrop color (Blue: #2563eb)
    color = (37, 99, 235, 255)
    
    # Define shape parameters
    cx = (size - 1) / 2.0
    # The circle part is at the bottom
    cy = size * 0.65 
    r = size * 0.3
    # The tip of the drop
    tip_y = size * 0.1
    
    # Calculate fill level (y-coordinate)
    # 0% = bottom of circle, 100% = tip
    bottom_y = cy + r
    fill_y = bottom_y - (percent / 100.0) * (bottom_y - tip_y)
    
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            
            in_shape = False
            # 1. Check if in the bottom circle
            if dy >= 0:
                if math.sqrt(dx*dx + dy*dy) <= r:
                    in_shape = True
            # 2. Check if in the top triangle/cone
            elif y >= tip_y:
                # Linear interpolation of width from tip to circle equator
                # At y = tip_y, width = 0
                # At y = cy, width = r
                width_at_y = r * (y - tip_y) / (cy - tip_y)
                if abs(dx) <= width_at_y:
                    in_shape = True
            
            if in_shape:
                # Draw outline
                is_outline = False
                if dy >= 0:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if r - 1.0 <= dist <= r:
                        is_outline = True
                elif y >= tip_y:
                    width_at_y = r * (y - tip_y) / (cy - tip_y)
                    if abs(abs(dx) - width_at_y) < 0.8:
                        is_outline = True
                
                if is_outline:
                    pixels[x, y] = color
                elif y >= fill_y:
                    pixels[x, y] = color

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_hourly_data(onecall):
    """Extract next 8 hours of temperature and rain data"""
    hourly_data = []
    temps = []
    
    # First pass: collect all temps
    for i in range(8):
        hour_data = onecall['hourly'][i]
        temps.append(int(hour_data['temp']))
    
    # Calculate min/max for scaling
    min_temp = min(temps)
    max_temp = max(temps)
    temp_range = max_temp - min_temp if max_temp > min_temp else 1
    
    # Second pass: build data with scaled positions
    for i in range(8):
        hour_data = onecall['hourly'][i]
        hour_time = datetime.fromtimestamp(hour_data['dt']).strftime("%H")
        temp = int(hour_data['temp'])
        rain_prob = int(hour_data.get('pop', 0) * 100)
        
        # Scale temperature to 0-100 range for positioning
        temp_position = int(((temp - min_temp) / temp_range) * 100)
        
        hourly_data.append({
            'hour': hour_time,
            'temp': temp,
            'rain': rain_prob,
            'raindrop_icon': draw_raindrop(rain_prob, size=24),
            'temp_position': 100 - temp_position  # Invert so high temps are at top
        })
    
    return hourly_data

def get_weather_data():
    """Get weather data as dictionary for HTML template"""
    settings = load_settings()
    weather_config = settings['openweather']
    API_KEY = weather_config['api_key']
    CITY = weather_config['city']
    UNITS = weather_config['units']
    
    try:
        # Fetch current weather for coordinates
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units={UNITS}"
        current = requests.get(current_url).json()
        
        # Get coordinates for One Call API
        lat = current['coord']['lat']
        lon = current['coord']['lon']
        
        # Fetch One Call API for moon phase and daily forecast
        onecall_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={API_KEY}&units={UNITS}&exclude=minutely,alerts"
        onecall = requests.get(onecall_url).json()
        
        # Current weather
        temp = current['main']['temp']
        feels_like = current['main']['feels_like']
        humidity = current['main']['humidity']
        wind_speed = current['wind']['speed']
        pressure = current['main']['pressure']
        weather_main = current['weather'][0]['main']
        desc = current['weather'][0]['description'].capitalize()
        
        # Sunrise and sunset
        sunrise_ts = current['sys']['sunrise']
        sunset_ts = current['sys']['sunset']
        sunrise_time = datetime.fromtimestamp(sunrise_ts).strftime("%H:%M")
        sunset_time = datetime.fromtimestamp(sunset_ts).strftime("%H:%M")
        
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%a, %b %d")
        
        # Get days 1-3 (skip today, show tomorrow and next 2 days)
        forecast_list = []
        for day in onecall['daily'][1:5]:
            dt = datetime.fromtimestamp(day['dt'])
            icon_code = day['weather'][0]['icon']
            
            # Convert moon phase to illumination percentage
            # Phase: 0/1 = new moon, 0.5 = full moon
            # Illumination: 0% = new, 100% = full
            moon_phase = day['moon_phase']
            moon_illumination = int((1 - abs(moon_phase - 0.5) * 2) * 100)
            
            forecast_list.append({
                'name': dt.strftime("%a"),
                'min': int(day['temp']['min']),
                'max': int(day['temp']['max']),
                'icon': get_icon_base64(icon_code),
                'moon_phase': moon_illumination,
                'moon_icon': draw_moon_phase(moon_phase, size=24)
            })
        
        # Get weather icon
        weather_icon_code = current['weather'][0]['icon']
        
        # Get visibility (in meters, convert to km)
        visibility = current.get('visibility', 10000) / 1000  # Default 10km if not available
        
        # Get UV index from One Call API
        uv_index = onecall['current'].get('uvi', 0)
        
        # Get moon phase
        moon_phase = get_moon_phase()
        
        return {
            'city': CITY.split(',')[0],  # Remove country code
            'date': current_date,
            'time': current_time,
            'temp': int(temp),
            'feels_like': int(feels_like),
            'icon': get_icon_base64(weather_icon_code),
            'description': desc,
            'wind': wind_speed,
            'humidity': humidity,
            'pressure': pressure,
            'airquality': 'Good',  # OpenWeather free tier doesn't provide AQI
            'visibility': f"{visibility:.1f}",
            'uv_index': f"{uv_index:.1f}",
            'sunrise': sunrise_time,
            'sunset': sunset_time,
            'wind_icon': get_icon_base64('wind'),
            'humidity_icon': get_icon_base64('humidity'),
            'pressure_icon': get_icon_base64('pressure'),
            'aqi_icon': get_icon_base64('aqi'),
            'visibility_icon': get_icon_base64('visibility'),
            'uvi_icon': get_icon_base64('uvi'),
            'sunrise_icon': get_icon_base64('sunrise'),
            'sunset_icon': get_icon_base64('sunset'),
            'moon_phase': moon_phase,
            'forecast': forecast_list,
            'hourly': get_hourly_data(onecall)
        }
        
    except Exception as e:
        print(f"Weather error: {e}")
        return {
            'city': CITY,
            'date': datetime.now().strftime("%a, %b %d"),
            'time': datetime.now().strftime("%H:%M"),
            'temp': 0,
            'icon': '❓',
            'description': 'Error loading weather',
            'wind': 0,
            'humidity': 0,
            'forecast': []
        }

def draw_weather_icon(draw, x, y, size, weather_main):
    """Draw a simple weather icon"""
    # Simple circle for sun, cloud shape for clouds, etc.
    if weather_main == 'Clear':
        # Draw sun
        center = (x + size//2, y + size//2)
        draw.ellipse([x+10, y+10, x+size-10, y+size-10], fill='#FFD700', outline='#FFA500', width=2)
    elif weather_main in ['Clouds', 'Mist', 'Fog', 'Haze']:
        # Draw cloud
        draw.ellipse([x+5, y+15, x+35, y+40], fill='#B0B0B0')
        draw.ellipse([x+20, y+10, x+50, y+35], fill='#B0B0B0')
        draw.ellipse([x+35, y+15, x+65, y+40], fill='#B0B0B0')
    elif weather_main in ['Rain', 'Drizzle']:
        # Draw cloud with rain
        draw.ellipse([x+5, y+10, x+30, y+30], fill='#808080')
        draw.ellipse([x+20, y+5, x+45, y+25], fill='#808080')
        draw.line([(x+10, y+32), (x+8, y+45)], fill='#4169E1', width=2)
        draw.line([(x+25, y+32), (x+23, y+45)], fill='#4169E1', width=2)
        draw.line([(x+40, y+32), (x+38, y+45)], fill='#4169E1', width=2)
    elif weather_main == 'Snow':
        # Draw snowflake
        draw.line([(x+35, y+10), (x+35, y+50)], fill='#87CEEB', width=2)
        draw.line([(x+15, y+30), (x+55, y+30)], fill='#87CEEB', width=2)
        draw.line([(x+20, y+15), (x+50, y+45)], fill='#87CEEB', width=2)
        draw.line([(x+50, y+15), (x+20, y+45)], fill='#87CEEB', width=2)

def get_weather_image(width, height):
    """Create weather display with current conditions and hourly forecast graph"""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    try:
        # Fetch current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units={UNITS}"
        current = requests.get(current_url).json()
        
        # Fetch hourly forecast (for graph)
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units={UNITS}"
        forecast_data = requests.get(forecast_url).json()
        
        # Current weather data
        temp = current['main']['temp']
        humidity = current['main']['humidity']
        wind_speed = current['wind']['speed']
        weather_main = current['weather'][0]['main']
        desc = current['weather'][0]['description'].capitalize()
        
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%a, %b %d")
        
        # === LAYOUT ===
        
        # Title: Location
        draw.text((20, 15), CITY, fill="black")
        
        # Date and Time
        draw.text((20, 40), current_date, fill="gray")
        draw.text((20, 60), current_time, fill="gray")
        
        # Weather Icon (left side)
        draw_weather_icon(draw, 20, 90, 70, weather_main)
        
        # Big Temperature (center-left)
        draw.text((110, 95), f"{temp:.0f}°", fill="black")
        
        # Weather description
        draw.text((110, 140), desc, fill="gray")
        
        # Wind and Humidity (lower section)
        draw.text((20, 180), f"Wind: {wind_speed} m/s", fill="gray")
        draw.text((120, 180), f"Humidity: {humidity}%", fill="gray")
        
        # === FORECAST GRAPH ===
        # Get next 8 forecast entries (24 hours, 3-hour intervals)
        forecast_entries = forecast_data['list'][:8]
        
        # Graph dimensions (reduced height)
        graph_x = 30
        graph_y = 220
        graph_width = width - 60
        graph_height = 90
        
        # Draw graph axes
        draw.line([(graph_x, graph_y), (graph_x, graph_y + graph_height)], fill="black", width=1)
        draw.line([(graph_x, graph_y + graph_height), (graph_x + graph_width, graph_y + graph_height)], fill="black", width=1)
        
        # Calculate data for graph
        times = []
        temps = []
        rain_probs = []
        
        for entry in forecast_entries:
            dt = datetime.fromtimestamp(entry['dt'])
            times.append(dt.strftime("%H"))
            temps.append(entry['main']['temp'])
            # Rain probability (pop = probability of precipitation)
            rain_probs.append(entry.get('pop', 0) * 100)
        
        if temps and rain_probs:
            # Temperature line (scale to graph)
            temp_min = min(temps)
            temp_max = max(temps)
            temp_range = temp_max - temp_min if temp_max - temp_min > 0 else 1
            
            # Draw temperature line
            temp_points = []
            for i, temp in enumerate(temps):
                x = graph_x + (i * graph_width // (len(temps) - 1)) if len(temps) > 1 else graph_x
                y_norm = (temp - temp_min) / temp_range
                y = graph_y + graph_height - int(y_norm * (graph_height - 20))
                temp_points.append((x, y))
            
            # Draw temperature line in red
            for i in range(len(temp_points) - 1):
                draw.line([temp_points[i], temp_points[i+1]], fill='#FF6B6B', width=2)
            
            # Draw rain bars in blue
            for i, rain in enumerate(rain_probs):
                x = graph_x + (i * graph_width // len(rain_probs))
                bar_height = int(rain * (graph_height - 20) / 100)
                y_top = graph_y + graph_height - bar_height
                draw.rectangle([x, y_top, x+12, graph_y + graph_height], fill='#4ECDC4', outline='#45B7D1')
            
            # Draw time labels
            for i, time in enumerate(times):
                if i % 2 == 0:  # Show every other label to avoid crowding
                    x = graph_x + (i * graph_width // len(times))
                    draw.text((x-5, graph_y + graph_height + 5), time, fill="gray")
        
        # Legend
        draw.rectangle([graph_x + graph_width - 100, graph_y - 15, graph_x + graph_width - 90, graph_y - 10], fill='#FF6B6B')
        draw.text((graph_x + graph_width - 85, graph_y - 18), "Temp", fill="gray")
        
        draw.rectangle([graph_x + graph_width - 50, graph_y - 15, graph_x + graph_width - 40, graph_y - 10], fill='#4ECDC4')
        draw.text((graph_x + graph_width - 35, graph_y - 18), "Rain %", fill="gray")
        
        # === 3-DAY FORECAST ===
        forecast_y = graph_y + graph_height + 30
        draw.line([(20, forecast_y), (width-20, forecast_y)], fill="gray", width=1)
        draw.text((20, forecast_y + 5), "3-Day Forecast", fill="black")
        
        # Process daily forecasts - get min/max temps for next 3 days
        daily_data = {}
        for entry in forecast_data['list']:
            dt = datetime.fromtimestamp(entry['dt'])
            date_key = dt.strftime("%Y-%m-%d")
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'temps': [],
                    'weather': entry['weather'][0]['main'],
                    'date': dt
                }
            
            daily_data[date_key]['temps'].append(entry['main']['temp'])
        
        # Get first 3 days
        daily_forecasts = []
        for date_key in sorted(daily_data.keys())[:3]:
            data = daily_data[date_key]
            daily_forecasts.append({
                'day': data['date'].strftime("%a"),
                'min': min(data['temps']),
                'max': max(data['temps']),
                'weather': data['weather']
            })
        
        # Display 3 days in a row
        day_width = (width - 40) // 3
        for i, day_data in enumerate(daily_forecasts):
            x_pos = 20 + (i * day_width)
            y_pos = forecast_y + 30
            
            # Day name
            draw.text((x_pos + 35, y_pos), day_data['day'], fill="black")
            
            # Weather icon (smaller)
            draw_weather_icon(draw, x_pos, y_pos + 25, 50, day_data['weather'])
            
            # Min/Max temps
            draw.text((x_pos + 60, y_pos + 35), f"{day_data['max']:.0f}°", fill="black")
            draw.text((x_pos + 60, y_pos + 55), f"{day_data['min']:.0f}°", fill="gray")
        
    except Exception as e:
        draw.text((20, 20), "Weather Error", fill="red")
        draw.text((20, 50), str(e)[:40], fill="red")
        print(f"Weather error: {e}")

    return img