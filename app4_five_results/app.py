import os
import re
import mysql.connector
from flask import Flask, request, render_template
from markupsafe import Markup
from dotenv import load_dotenv
from datetime import datetime
import webbrowser
import threading
from collections import defaultdict

# Load env vars
load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

print("Looking for image at:", os.path.abspath("static/images/background_new.jpg"))
print("Exists:", os.path.exists("static/images/background_new.jpg"))

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def extract_course_name_from_file(folder=None):
    if folder is None:
        folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print("📂 Scanning directory:", folder)

    try:
        for filename in os.listdir(folder):
            print("🔎 Checking file:", filename)
            if filename.endswith("Callaway scoring sheet.xlsx"):
                parts = filename.split()
                if len(parts) >= 5:
                    course_name = " ".join(parts[:-5])
                    print(f"✅ Matched course name: {course_name}")
                    return course_name
    except Exception as e:
        print("❌ Error scanning files:", e)

    print("❌ No Callaway scoring sheet found.")
    return "Unknown Course"

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
        SELECT DISTINCT f.first_name, f.last_name, f.handicap, f.{order_by_field}, f.{order_by_field}_net, {order_by_clause}
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
    course_name = extract_course_name_from_file()
    formatted_date = datetime.today().strftime("%B %d, %Y")
    results = {
        "Top Overall Juniors": fetch_ranked_results("f.juniors > 0", "total", junior_n),
        "Top Front 9 Juniors": fetch_ranked_results("f.juniors > 0", "front_9", junior_n),
        "Top Back 9 Juniors": fetch_ranked_results("f.juniors > 0", "back_9", junior_n),
        "Top Overall Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "total", senior_n),
        "Top Front 9 Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "front_9", senior_n),
        "Top Back 9 Seniors/Ladies": fetch_ranked_results("f.seniors_ladies > 0", "back_9", senior_n)
    }

    html = """
    <div class="toggle-buttons" style="text-align:center; margin: 20px 0;">
        <button onclick="toggleAll(true)">Expand All 🔼</button>
        <button onclick="toggleAll(false)">Collapse All 🔽</button>
    </div>
    <hr>
"""

    for title, rows in results.items():
        html += f"""
        <div class='leaderboard-wrapper leaderboard-card'>
            <h2 class='collapsible-header' onclick='toggleCollapse(this)'>
                <span class='icon'>🏅</span> {title}
                <span class='collapse-icon'>🔽</span>
            </h2>
            <div class='collapsible-content'>
                <table class='themed-table'>
                    <thead>
                        <tr><th>Place</th><th>Name</th><th>HCP</th><th>Score</th><th>Net</th></tr>
                    </thead>
                    <tbody>
        """

        # Reset tie rank tracking per section
        tie_counts = defaultdict(int)

        for idx, row in enumerate(rows):
            row_class = "even-row" if (idx + 1) % 2 == 0 else ""

            net_score = round(float(row[4]), 1)
            tie_group = [r for r in rows if round(float(r[4]), 1) == net_score]
            is_tie = len(tie_group) > 1

            badge = ""
            if is_tie:
                tie_counts[net_score] += 1
                tie_rank = tie_counts[net_score]
                color_class = f"tie-badge-{tie_rank}" if tie_rank <= 5 else "tie-badge"
                badge = f"<span class='tie-badge {color_class}' title='Tiebreak Rank'>{tie_rank}</span>"

            name_with_badge = f"<span class='player-name-with-check'><span class='player-name'>{row[0]} {row[1]}</span>{badge}</span>"
            html += f"<tr class='{row_class}'><td>{idx + 1}</td><td>{name_with_badge}</td><td>{format_number(row[2])}</td><td>{format_number(row[3])}</td><td><strong>{format_number(row[4])}</strong></td></tr>"

        html += "</tbody></table></div></div>"

    return Markup(html)

@app.route("/", methods=["GET", "POST"])
def index():
    course_name = extract_course_name_from_file()
    formatted_date = datetime.today().strftime("%B %d, %Y")

    if request.method == "POST":
        try:
            juniors = int(request.form["juniors"])
            seniors = int(request.form["seniors"])
            html = build_leaderboard_html(juniors, seniors)
            return render_template("five_results.html", content=html, course_name=course_name, course_date=formatted_date)
        except ValueError:
            return "Please enter valid numbers.", 400

    return render_template("five_input.html", course_name=course_name, date=formatted_date)

if __name__ == "__main__":
    def open_browser():
        webbrowser.open("http://localhost:5001/")

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, open_browser).start()

    app.run(port=5001, debug=True)
