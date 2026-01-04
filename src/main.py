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
    runs_data = strava.get_runs_data()
    
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
        runs=runs_data,
        css_content=css_content
    )
    
    return html_content

def main():
    print("Creating e-ink dashboard...")
    
    # Create HTML dashboard
    html_content = create_dashboard_html()
    
    # Determine output directory: /output for container, current dir for local
    if os.path.exists('/output') and os.path.isdir('/output'):
        output_dir = '/output'
    else:
        output_dir = os.getcwd()
    
    temp_file = os.path.join(output_dir, "temp_render.png")
    output_file = os.path.join(output_dir, OUTPUT_FILE)
    
    # Render HTML to image at larger size to avoid bottom margin issue
    # Configure for headless operation (no X server needed)
    hti = Html2Image(
        output_path=output_dir,
        custom_flags=[
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--disable-extensions',
            '--disable-features=NetworkService',
            '--disable-background-networking',
            '--disable-sync',
            '--force-device-scale-factor=1',  # Disable any scaling
            '--font-render-hinting=none',  # Disable font hinting
            '--disable-lcd-text'  # Disable subpixel rendering
        ]
    )
    hti.screenshot(
        html_str=html_content,
        save_as="temp_render.png",
        size=(DISPLAY_WIDTH, DISPLAY_HEIGHT + 120)  # Render extra height
    )
    
    # Crop to exact size and convert to palette mode for cleaner colors
    img = PILImage.open(temp_file)
    img_cropped = img.crop((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT))
    
    # Convert to RGB first (in case it's RGBA), then to palette mode
    # This reduces color variations and makes it more suitable for e-ink
    if img_cropped.mode == 'RGBA':
        # Create white background for transparent areas
        background = PILImage.new('RGB', img_cropped.size, 'white')
        background.paste(img_cropped, mask=img_cropped.split()[3])  # Use alpha channel as mask
        img_cropped = background
    
    # Convert to palette mode with adaptive colors (will reduce to distinct colors)
    # This eliminates anti-aliasing artifacts by forcing discrete colors
    img_palette = img_cropped.convert('P', palette=PILImage.ADAPTIVE, colors=256)
    img_palette = img_palette.convert('RGB')  # Convert back to RGB for display
    
    img_palette.save(output_file, optimize=False)  # Disable optimization to avoid quality loss
    
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
            inky_display.set_image(dashboard, saturation=0.5)
            inky_display.show()
            print("Dashboard pushed to Inky Impression 2025!")
        except Exception as e:
            print(f"E-ink display error: {e}")

if __name__ == "__main__":
    main()
