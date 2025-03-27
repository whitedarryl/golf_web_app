import os
import re
import mysql.connector
from flask import Flask, request, render_template
from markupsafe import Markup
from dotenv import load_dotenv
from datetime import datetime
import webbrowser
import threading

# Load env vars
load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

app = Flask(__name__)

def get_latest_course():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT course_name, date_played 
        FROM courses 
        WHERE course_id = (SELECT MAX(course_id) FROM courses)
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        course_name = result[0]
        raw_date = result[1].strftime("%Y-%m-%d")
        formatted = format_date(raw_date)
        return course_name, formatted, raw_date
    return "Unknown", "Unknown", "0000-00-00"

def format_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        day = date_obj.day
        suffix = "th" if 10 <= day % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{date_obj.strftime('%B')} {day}{suffix}, {date_obj.year}"
    except:
        return "Invalid Date"

def format_number(value):
    try:
        value = float(value)
        return f"{int(value)}" if value.is_integer() else f"{value:.1f}"
    except:
        return value

def fetch_ranked_results(filter_condition, order_by_field, top_n):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hole_number FROM course_hole_handicap
        WHERE course_id = (SELECT MAX(course_id) FROM course_hole_handicap)
        ORDER BY handicap_rank ASC
    """)
    handicap_holes = [f"s.hole_{row[0]}" for row in cursor.fetchall()]
    order_by_clause = ", ".join(handicap_holes) if handicap_holes else f"f.{order_by_field}_net"

    query = f"""
        SELECT f.first_name, f.last_name, f.handicap, f.{order_by_field}, f.{order_by_field}_net, {order_by_clause}
        FROM fives f
        JOIN scores s ON f.first_name = s.first_name AND f.last_name = s.last_name
        WHERE {filter_condition}
        ORDER BY f.{order_by_field}_net ASC, {order_by_clause} ASC
        LIMIT %s
    """
    cursor.execute(query, (top_n,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def build_leaderboard_html(junior_n, senior_n):
    course, formatted_date, raw_date = get_latest_course()
    results = {
        "👦 Top Overall Juniors": fetch_ranked_results("f.juniors > 0", "total", junior_n),
        "👦 Top Front 9 Juniors": fetch_ranked_results("f.juniors > 0", "front_9", junior_n),
        "👦 Top Back 9 Juniors": fetch_ranked_results("f.juniors > 0", "back_9", junior_n),
        "🧓 Top Overall Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "total", senior_n),
        "🧓 Top Front 9 Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "front_9", senior_n),
        "🧓 Top Back 9 Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "back_9", senior_n)
    }

    html = f"<h1>🏌️ Tony G's {course} - Five Five & Five</h1><h3>{formatted_date}</h3><hr>"
    for title, rows in results.items():
        html += f"<div class='table-container'><h4>{title}</h4><table class='table table-bordered table-sm'><thead><tr><th>Place</th><th>Name</th><th>HCP</th><th>Score</th><th>Net</th></tr></thead><tbody>"
        for idx, row in enumerate(rows, start=1):
            html += f"<tr><td>{idx}</td><td>{row[0]} {row[1]}</td><td>{format_number(row[2])}</td><td>{format_number(row[3])}</td><td>{format_number(row[4])}</td></tr>"
        html += "</tbody></table></div>"
    return Markup(html)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            juniors = int(request.form["juniors"])
            seniors = int(request.form["seniors"])
            html = build_leaderboard_html(juniors, seniors)
            return render_template("five_results.html", content=html)
        except ValueError:
            return "Please enter valid numbers.", 400
    return render_template("five_input.html")

if __name__ == "__main__":
    def open_browser():
        webbrowser.open("http://localhost:5005/")

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, open_browser).start()

    app.run(port=5005, debug=True)

