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
TEST_MODE = True

def create_dashboard_html():
    """Create the dashboard using HTML templates"""
    
    # Get weather data
    weather_data = weather.get_weather_data()
    
    # Get strava data
    runs_data = strava.get_runs_data()
    
    # Load CSS file
    css_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.css')
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    # Load HTML template
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
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
    
    # Render HTML to image at larger size to avoid bottom margin issue
    temp_file = "temp_render.png"
    hti = Html2Image(output_path=os.path.dirname(__file__))
    hti.screenshot(
        html_str=html_content,
        save_as=temp_file,
        size=(DISPLAY_WIDTH, DISPLAY_HEIGHT + 120)  # Render extra height
    )
    
    # Crop to exact size
    img = PILImage.open(temp_file)
    img_cropped = img.crop((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT))
    img_cropped.save(OUTPUT_FILE)
    
    # Clean up temp file
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    print(f"Dashboard saved to {OUTPUT_FILE}")
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
