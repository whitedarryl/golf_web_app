from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from datetime import datetime
import re
import os

# Load env vars
load_dotenv()

# Init Flask
app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

# Config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "golf-dev-key")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Register Blueprints
from app1_golf_score_calculator import score_calc_bp
app.register_blueprint(score_calc_bp)

# Root route
@app.route("/")
def landing():
    course_name, course_date = extract_course_info_from_filename()
    session["course_name"] = course_name
    session["course_date"] = course_date
    print("🏌️ Landing set course:", course_name)
    return render_template("index.html", course_name=course_name, course_date=course_date)

def home():
    return render_template("index.html")

# Route for AJAX test
@app.route("/run_scripts", methods=["POST"])
def run_scripts():
    data = request.get_json()
    course_name = data.get("course_name")
    course_date = data.get("course_date")

    if not course_name or not course_date:
        return jsonify(success=False, message="Missing course name or date"), 400

    print(f"✅ Running scripts for {course_name} on {course_date}")
    return jsonify(success=True)

def extract_course_info_from_filename():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pattern = r"^(.*?)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\s+Callaway scoring sheet\.xls[x]?$"

    for file in os.listdir(root_dir):
        match = re.match(pattern, file)
        if match:
            course_name = match.group(1)
            print(f"✅ Match found! Course: {course_name}")
            return course_name, None

    print("⚠️ No matching file found.")
    return "Unknown Course", None

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
