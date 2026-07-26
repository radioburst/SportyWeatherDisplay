from html2image import Html2Image
from jinja2 import Template
from PIL import Image as PILImage
import weather
import strava
import os

# Configuration
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
OUTPUT_FILE = "eink_display_preview.png"
# Default to false - will push to display unless explicitly set to 'true'
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

def create_dashboard_html():
    """Create the dashboard using HTML templates"""
    
    # Get weather data
    weather_data = weather.get_weather_data()
    
    # Get strava data
    activities_data = strava.get_activities_data()
    monthly_stats = strava.get_monthly_stats()
    
    # Get paths relative to src directory
    src_dir = os.path.dirname(__file__)
    
    # Load CSS file
    css_path = os.path.join(src_dir, 'templates', 'dashboard.css')
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    # Load HTML template
    template_path = os.path.join(src_dir, 'templates', 'dashboard.html')
    with open(template_path, 'r') as f:
        template = Template(f.read())
    
    # Render HTML with data
    html_content = template.render(
        weather=weather_data,
        activities=activities_data,
        monthly_stats=monthly_stats,
        css_content=css_content
    )
    
    return html_content

def main():
    print("Creating e-ink dashboard...")
    
    # Create HTML dashboard
    html_content = create_dashboard_html()
    
    # Determine output directory
    config_output = os.path.expanduser('~/.config/sporty-weather/output')
    if os.path.exists('/output') and os.path.isdir('/output'):
        output_dir = '/output'
    elif os.path.exists(config_output) and os.path.isdir(config_output):
        output_dir = config_output
    else:
        output_dir = os.getcwd()
    
    temp_file = os.path.join(output_dir, "temp_render.png")
    output_file = os.path.join(output_dir, OUTPUT_FILE)
    
    # Set fontconfig environment variable to disable anti-aliasing on Linux
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.environ['FONTCONFIG_FILE'] = os.path.join(project_root, 'fonts.conf')
    
    # Detect if we are running in a display environment (like Xvfb or Desktop)
    # If a display is available, we can disable headless mode for better font rendering
    has_display = 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ
    
    # Fallback for RPi Desktop: If running via SSH or Service, DISPLAY might be missing
    # but the X server is usually running on :0
    if not has_display and os.path.exists('/tmp/.X11-unix/X0'):
        os.environ['DISPLAY'] = ':0'
        has_display = True
        print("Detected local X11 server on :0, using it for better font rendering")
    
    # Render HTML to image at native resolution
    # Simplified flags for Raspberry Pi 4
    chrome_flags = [
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--force-device-scale-factor=1',
        '--window-size=800,800',
        '--hide-scrollbars',
        '--mute-audio',
        '--no-first-run',
        '--disable-setuid-sandbox'
    ]
    
    if not has_display:
        chrome_flags.append('--headless')
        print("No display detected, using --headless mode")
    else:
        display_val = os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        print(f"Display detected ({display_val}), disabling --headless for better font rendering")

    # Try to find chromium executable
    browser_path = None
    for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome']:
        if os.path.exists(path):
            browser_path = path
            break
    
    if browser_path:
        print(f"Using browser: {browser_path}")
        hti = Html2Image(
            browser_executable=browser_path,
            output_path=output_dir,
            custom_flags=chrome_flags
        )
    else:
        hti = Html2Image(
            output_path=output_dir,
            custom_flags=chrome_flags
        )

    print("Rendering dashboard to image...")
    try:
        hti.screenshot(
            html_str=html_content,
            save_as="temp_render.png",
            size=(DISPLAY_WIDTH, DISPLAY_HEIGHT + 120)
        )
    except Exception as e:
        print(f"❌ Rendering error: {e}")

    # Check if file was actually created
    if not os.path.exists(temp_file):
        print(f"❌ Error: Screenshot failed! {temp_file} was not created.")
        return

    # Crop to exact size
    img = PILImage.open(temp_file)
    img_cropped = img.crop((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT))
    
    # Convert to RGB first (in case it's RGBA)
    if img_cropped.mode == 'RGBA':
        # Create white background for transparent areas
        background = PILImage.new('RGB', img_cropped.size, 'white')
        background.paste(img_cropped, mask=img_cropped.split()[3])  # Use alpha channel as mask
        img_cropped = background
    elif img_cropped.mode != 'RGB':
        img_cropped = img_cropped.convert('RGB')
    
    img_cropped.save(output_file, optimize=False)
    
    # Clean up temp file
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    print(f"Dashboard saved to {output_file}")
    print("Open the file to preview the display")
    
    if not TEST_MODE:
        # Push to actual e-ink display (Inky Impression 2025 - PIM773, 6-color)
        try:
            from inky.inky_e673 import Inky
            from PIL import Image
            
            # Initialize Inky Impression 2025 (800x480, 6-color Spectra)
            # This is the E673 controller for the 7.3" 2025 edition
            inky_display = Inky()
            
            # Load and display the image
            dashboard = Image.open(output_file)
            inky_display.set_image(dashboard, saturation=0.1)
            inky_display.show()
            print("Dashboard pushed to Inky Impression 2025!")
        except Exception as e:
            print(f"E-ink display error: {e}")

if __name__ == "__main__":
    main()
