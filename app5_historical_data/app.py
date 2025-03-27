from flask import Flask, render_template, request
import mysql.connector
import os
import webbrowser
import threading
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Populate dropdowns
    cursor.execute("SELECT DISTINCT course_name FROM courses ORDER BY course_name;")
    courses = [row['course_name'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT first_name, last_name FROM scores_archive ORDER BY last_name, first_name;")
    players = [f"{row['first_name']} {row['last_name']}" for row in cursor.fetchall()]

    results = []
    selected_player = None
    selected_course = None

    if request.method == 'POST':
        player = request.form['player']
        course = request.form['course']
        selected_player = player
        selected_course = course
        parts = player.strip().split()
        first_name = " ".join(parts[:-1])
        last_name = parts[-1]


        cursor.execute("""
            SELECT sa.first_name, sa.last_name, sa.total, DATE_FORMAT(cs.date_played, '%m-%d-%Y') AS date_played
            FROM scores_archive sa
            JOIN course_snapshot cs ON sa.snapshot_id = cs.snapshot_id
            WHERE sa.first_name = %s AND sa.last_name = %s AND cs.course_name = %s
            ORDER BY cs.date_played ASC;
        """, (first_name, last_name, course))
        
        results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        players=players,
        courses=courses,
        results=results,
        selected_player=selected_player,
        selected_course=selected_course
    )

if __name__ == '__main__':
    port = 5006
    url = f"http://127.0.0.1:{port}"

    # Only open browser on the actual first run, not the reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, lambda: webbrowser.open_new_tab(url)).start()

    app.run(debug=True, host='0.0.0.0', port=port)


