from staticmap import StaticMap, Line, CircleMarker
from PIL import Image, ImageDraw, ImageFont
from stravalib.client import Client
from datetime import datetime, timedelta
import gpxpy
import polyline
import base64
import io
import os
import json
import time
import requests

# Path to settings file
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_settings():
    """Load settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    raise FileNotFoundError(f"Settings file not found: {SETTINGS_FILE}")

def save_settings(settings):
    """Save settings to JSON file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def refresh_access_token():
    """Refresh the access token using the refresh token"""
    settings = load_settings()
    strava = settings['strava']
    
    # Check if token needs refresh (expires within next 5 minutes)
    if strava['expires_at'] > time.time() + 300:
        return strava['access_token']
    
    # Refresh the token
    refresh_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': strava['client_id'],
        'client_secret': strava['client_secret'],
        'grant_type': 'refresh_token',
        'refresh_token': strava['refresh_token']
    }
    
    try:
        response = requests.post(refresh_url, data=payload)
        response.raise_for_status()
        new_tokens = response.json()
        
        # Update tokens
        strava['access_token'] = new_tokens['access_token']
        strava['refresh_token'] = new_tokens['refresh_token']
        strava['expires_at'] = new_tokens['expires_at']
        settings['strava'] = strava
        
        save_settings(settings)
        return strava['access_token']
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return strava['access_token']  # Return old token as fallback

def get_stat_icon(icon_name):
    """Convert stat icon to base64 data URI"""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', f'{icon_name}.png')
    if os.path.exists(icon_path):
        with open(icon_path, 'rb') as f:
            img_data = f.read()
            img_str = base64.b64encode(img_data).decode()
            return f"data:image/png;base64,{img_str}"
    return None

def get_strava_client():
    """Initialize Strava client with access token"""
    access_token = refresh_access_token()
    client = Client(access_token=access_token)
    return client

def get_runs_data():
    """Get runs data as list of dictionaries for HTML template"""
    colors = ['#fc5200', '#2563eb', '#10b981']  # Strava orange, Blue, Green
    
    try:
        client = get_strava_client()
        
        # Fetch last 3 run activities
        activities = client.get_activities(limit=10)
        runs = [act for act in activities if act.type == 'Run'][:3]
        
        runs_data = []
        
        for i, run in enumerate(runs):
            # Date
            date_str = run.start_date_local.strftime("%b %d")
            
            # Distance
            distance_km = float(run.distance) / 1000
            distance_str = f"{distance_km:.2f}km"
            
            # Duration
            total_seconds = int(run.moving_time)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_str = f"{minutes}:{seconds:02d}"
            
            # Pace
            if distance_km > 0:
                pace_seconds = total_seconds / distance_km
                pace_min = int(pace_seconds // 60)
                pace_sec = int(pace_seconds % 60)
                pace_str = f"{pace_min}:{pace_sec:02d}/km"
            else:
                pace_str = "N/A"
            
            # Elevation gain
            elevation = int(run.total_elevation_gain) if run.total_elevation_gain else 0
            elevation_str = f"{elevation}m"
            
            # Kudos count
            kudos = run.kudos_count if run.kudos_count else 0
            kudos_str = f"{kudos}"
            
            # Generate map as base64 data URI
            map_path = None
            if run.map.summary_polyline:
                try:
                    coordinates = polyline.decode(run.map.summary_polyline)
                    if coordinates:
                        # Create small map
                        m = StaticMap(290, 148, padding_x=5, padding_y=5,
                                    url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
                        
                        line_coords = [(lon, lat) for lat, lon in coordinates]
                        line = Line(line_coords, color=colors[i], width=3)
                        m.add_line(line)
                        
                        # Add markers
                        start_lon, start_lat = coordinates[0][1], coordinates[0][0]
                        m.add_marker(CircleMarker((start_lon, start_lat), '#00d46a', 6))
                        
                        end_lon, end_lat = coordinates[-1][1], coordinates[-1][0]
                        m.add_marker(CircleMarker((end_lon, end_lat), colors[i], 6))
                        
                        # Convert to base64
                        map_img = m.render()
                        buffered = io.BytesIO()
                        map_img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        map_path = f"data:image/png;base64,{img_str}"
                except Exception as e:
                    print(f"Map error for run {i}: {e}")
            
            runs_data.append({
                'date': date_str,
                'activity_icon': get_stat_icon('run'),
                'distance': distance_str,
                'distance_icon': get_stat_icon('distance'),
                'duration': duration_str,
                'duration_icon': get_stat_icon('time'),
                'pace': pace_str,
                'pace_icon': get_stat_icon('pace'),
                'elevation': elevation_str,
                'elevation_icon': get_stat_icon('elevation'),
                'kudos': kudos_str,
                'kudos_icon': get_stat_icon('heart'),
                'color': colors[i],
                'map_path': map_path
            })
        
        return runs_data
        
    except Exception as e:
        print(f"Strava error: {e}")
        return []

def get_runs_with_maps(width, height):
    """Display last 3 runs with stats and individual maps for each"""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    # Colors for each run
    colors = ['#fc5200', '#2563eb', '#10b981']  # Strava orange, Blue, Green
    
    try:
        client = get_strava_client()
        
        # Fetch last 3 run activities
        activities = client.get_activities(limit=10)
        runs = [act for act in activities if act.type == 'Run'][:3]
        
        if not runs:
            draw.text((10, 10), "No recent runs", fill="black")
            return img
        
        # Each run gets 160px height (480/3)
        run_height = height // 3
        
        for i, run in enumerate(runs):
            y_start = i * run_height
            
            # Draw separator line between runs
            if i > 0:
                draw.line([(0, y_start), (width, y_start)], fill="gray", width=1)
            
            # Stats section (left side, ~100px wide)
            stats_x = 15
            stats_y = y_start + 10
            
            # Color indicator
            draw.rectangle([(stats_x, stats_y), (stats_x + 4, stats_y + run_height -15)], fill=colors[i])
            
            # Date
            date_str = run.start_date_local.strftime("%b %d")
            draw.text((stats_x + 10, stats_y), date_str, fill="black")
            
            # Distance
            distance_km = float(run.distance) / 1000
            draw.text((stats_x + 10, stats_y + 20), f"{distance_km:.2f}km", fill="gray")
            
            # Duration
            total_seconds = int(run.moving_time)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            draw.text((stats_x + 10, stats_y + 40), f"{minutes}:{seconds:02d}", fill="gray")
            
            # Pace
            if distance_km > 0:
                pace_seconds = total_seconds / distance_km
                pace_min = int(pace_seconds // 60)
                pace_sec = int(pace_seconds % 60)
                draw.text((stats_x + 10, stats_y + 60), f"{pace_min}:{pace_sec:02d}/km", fill="gray")
            
            # Map section (right side, ~290px wide x 148px high)
            map_width = width - 110
            map_height = run_height - 10
            
            try:
                # Get map for this specific run
                if run.map.summary_polyline:
                    coordinates = polyline.decode(run.map.summary_polyline)
                    
                    if coordinates:
                        # Create small map
                        m = StaticMap(
                            map_width,
                            map_height,
                            padding_x=5,
                            padding_y=5,
                            url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                        )
                        
                        # Draw the route
                        line_coords = [(lon, lat) for lat, lon in coordinates]
                        line = Line(line_coords, color=colors[i], width=3)
                        m.add_line(line)
                        
                        # Add markers
                        start_lon, start_lat = coordinates[0][1], coordinates[0][0]
                        m.add_marker(CircleMarker((start_lon, start_lat), '#00d46a', 6))
                        
                        end_lon, end_lat = coordinates[-1][1], coordinates[-1][0]
                        m.add_marker(CircleMarker((end_lon, end_lat), colors[i], 6))
                        
                        # Render and paste
                        map_img = m.render()
                        img.paste(map_img, (105, y_start + 5))
                    else:
                        draw.text((110, y_start + 20), "No GPS data", fill="gray")
                else:
                    draw.text((110, y_start + 20), "No map", fill="gray")
            except Exception as e:
                draw.text((110, y_start + 20), "Map error", fill="red")
                print(f"Map error for run {i+1}: {e}")
        
    except Exception as e:
        draw.text((10, 10), f"Error: {str(e)[:50]}", fill="red")
        print(f"Strava API error: {e}")
    
    return img