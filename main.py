import sys
import os
import logging
from flask import Flask, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv()

from landing_page.app import app as landing_app
from config import ROUTES
from settings import CSS_FILE_PATH, STATIC_DIR
from app1_golf_score_calculator import score_calc_bp
from callaway_results_app import create_app as create_callaway_app
from app1_golf_score_calculator.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('FLASK_DEBUG') == 'True' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app instances
app = create_app()
callaway_app = create_callaway_app()

# Register routes
ROUTES["/golf_score_calculator"] = app
ROUTES["/callaway_results"] = callaway_app

logger.info("✅ All routes registered successfully")

# Validate critical files and directories
if not os.path.exists(STATIC_DIR):
    logger.error("Static directory not found: %s", STATIC_DIR)
    sys.exit(1)  # Exit the application if the static directory is missing

if not os.path.exists(CSS_FILE_PATH):
    logger.warning("CSS file not found: %s", CSS_FILE_PATH)  # Log a warning but don't exit

# Log the existence of the CSS file
logger.debug("🧪 File exists at %s? %s", CSS_FILE_PATH, os.path.exists(CSS_FILE_PATH))

# Log the static directory being used
logger.debug("Static directory being used: %s", landing_app.static_folder)

# Log the Flask static folder
logger.debug("Flask static folder: %s", landing_app.static_folder)
logger.debug("Flask static folder: %s", app.static_folder)

logger.debug("Fonts directory exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'fonts')))
logger.debug("Font file exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'fonts', 'Satisfy-Regular.woff2')))
logger.debug("Images directory exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'images')))
logger.debug("Background image exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'images', 'background.jpg')))

@app.before_request
def log_static_requests():
    if request.path.startswith('/static'):
        logger.debug("Static file requested: %s", request.path)

# Combine the landing app with other apps using DispatcherMiddleware
application = DispatcherMiddleware(landing_app, ROUTES)

with landing_app.app_context():
    print("\n📋 Registered Routes:")
    if hasattr(application, 'url_map'):
        for rule in application.url_map.iter_rules():
            print(f"{rule.methods} {rule.rule}")
    else:
        print("🚫 application has no 'url_map'.")

from config import ROUTES  # or wherever ROUTES is defined

print("\n📋 Registered Flask Apps and Their Routes:")
for path, app in ROUTES.items():
    print(f"\n🔹 App mounted at: {path}")
    try:
        for rule in app.url_map.iter_rules():
            print(f"  {rule.methods} {rule.rule}")
    except Exception as e:
        print(f"  🚫 Could not inspect app at {path}: {e}")


if __name__ == '__main__':
    # Determine the environment (default to 'production')
    environment = os.getenv('FLASK_ENV', 'production').lower()
    is_debug = environment == 'development'

    logger.info("Starting the application in %s mode on http://0.0.0.0:5001", environment)
    print("🚀 Registered Blueprints:", landing_app.blueprints)
    
    # Serve the combined app
    run_simple(
        '0.0.0.0',
        5001,
        application,           # 👈 use DispatcherMiddleware instance, not `app`
        use_reloader=is_debug,
        use_debugger=is_debug
    )

