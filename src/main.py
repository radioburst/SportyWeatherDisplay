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
TEST_MODE = os.environ.get('TEST_MODE', 'true').lower() == 'true'

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
    hti = Html2Image(output_path=output_dir)
    hti.screenshot(
        html_str=html_content,
        save_as="temp_render.png",
        size=(DISPLAY_WIDTH, DISPLAY_HEIGHT + 120)  # Render extra height
    )
    
    # Crop to exact size
    img = PILImage.open(temp_file)
    img_cropped = img.crop((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT))
    img_cropped.save(output_file)
    
    # Clean up temp file
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    print(f"Dashboard saved to {output_file}")
    print("Open the file to preview the display")
    
    if not TEST_MODE:
        # Push to actual e-ink display
        try:
            from inky.auto import auto
            from PIL import Image
            inky_display = auto()
            dashboard = Image.open(OUTPUT_FILE)
            inky_display.set_image(dashboard, saturation=0.5)
            inky_display.show()
            print("Dashboard pushed to e-ink display!")
        except Exception as e:
            print(f"E-ink display error: {e}")

if __name__ == "__main__":
    main()
