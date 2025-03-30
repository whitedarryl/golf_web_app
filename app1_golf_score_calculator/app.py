import os
import re
import atexit
from flask import Flask, session
from .routes import routes
from .utils.excel_session import close_excel

def extract_course_name_from_file(folder=None):
    if folder is None:
        folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("📂 Scanning directory:", folder)
    pattern = re.compile(
        r'^(.+?)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s+Callaway scoring sheet\.xls$',
        re.IGNORECASE
    )
    for filename in os.listdir(folder):
        print("🔎 Checking file:", filename)
        match = pattern.match(filename)
        if match:
            course_name = match.group(1)
            print("✅ Matched course name:", course_name)
            return course_name
    print("❌ No course file matched pattern.")
    return "Unknown Course"

def create_app():
    app = Flask(__name__)
    app.secret_key = "super-secret-key"

    @app.before_request
    def set_course():
        if 'course_name' not in session:
            session['course_name'] = extract_course_name_from_file()

    app.register_blueprint(routes, url_prefix='/')  # <---- notice it's "/"
    return app

app = create_app()