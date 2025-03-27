from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os

# Load .env variables if present
load_dotenv()

app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

# Config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "golf-dev-key")
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto reload in development

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run_scripts", methods=["POST"])
def run_scripts():
    data = request.get_json()
    course_name = data.get("course_name")
    course_date = data.get("course_date")

    if not course_name or not course_date:
        return jsonify(success=False, message="Missing course name or date"), 400

    # TODO: Add your backend script logic here
    print(f"✅ Running scripts for {course_name} on {course_date}")

    # Return fake success for now
    return jsonify(success=True)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# Entry point
if __name__ == "__main__":
    app.run(debug=True)
