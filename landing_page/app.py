from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
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
    today = datetime.today().strftime("%B %d, %Y")
    return render_template("index.html", current_date=today)

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

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
