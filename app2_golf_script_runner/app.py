from flask import Flask, render_template, request, jsonify
import subprocess
import sys
import mysql.connector
import os
import time
from dotenv import load_dotenv
import webbrowser
import threading

print("Using Python:", sys.executable)

app = Flask(__name__)

load_dotenv()

def run_script(script_name, args=None):
    try:
        working_dir = r"C:\\Golf"
        os.chdir(working_dir)

        command = [sys.executable, script_name]
        if args:
            command.extend(args)

        process = subprocess.run(command, check=True, text=True, capture_output=True)
        return process.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running {script_name}:\n{e.stderr}\n{e.stdout}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_scripts', methods=['POST'])
def run_scripts():
    course_name = request.form['course_name']
    course_date = request.form['course_date']
    
    # Connect to MySQL and truncate the fives table
    try:
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE fives;")
        conn.commit()
        cursor.close()
        conn.close()
        truncate_message = "Fives table truncated successfully."
    except Exception as e:
        truncate_message = f"Database error: {e}"

    scripts = [
        "convert_xlsx_to_csv.py",
        "convert_xlsx_to_csv_handicap_ranks.py",
        "extract_handicap_order.py",
        "import_golf_scores.py",
        "import_handicap_ranks.py",
        "fives_import.py"
    ]

    output_logs = []
    progress_updates = []

    for index, script in enumerate(scripts):
        progress_updates.append({"step": index + 1, "total": len(scripts), "script": script})
        if script in ["import_golf_scores.py", "import_handicap_ranks.py", "fives_import.py"]:
            output = run_script(script, args=[course_name, course_date])
        else:
            output = run_script(script)
        output_logs.append(f"{script}:\n{output}")
        time.sleep(1)  # Simulate progress
    
    return jsonify({"message": truncate_message, "logs": output_logs, "progress": progress_updates})

if __name__ == '__main__':
    port = 5000
    url = f"http://127.0.0.1:{port}"
    
    # Ensure only one tab opens
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, lambda: webbrowser.open_new_tab(url)).start()
    
    app.run(debug=True, host='0.0.0.0', port=port)
