import os
import mysql.connector
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
import webbrowser
import threading

# ✅ Load environment variables
load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

app = Flask(__name__)

def get_latest_course():
    """Retrieve the most recent course name and date from the database."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    query = """
        SELECT course_name, date_played 
        FROM courses 
        WHERE course_id = (SELECT MAX(course_id) FROM courses);
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return {"course_name": result[0], "date_played": result[1].strftime("%Y-%m-%d")}
    return {"course_name": "Unknown Course", "date_played": "0000-00-00"}

def fetch_ranked_results(order_by_field, exclude_winners=False, winners=None, top_n=5):
    """Fetch top players by total or net score, with optional winner exclusion and tie-breaking."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Get tie-breaking order from course hole handicap
    cursor.execute("""
        SELECT hole_number FROM course_hole_handicap
        WHERE course_id = (SELECT MAX(course_id) FROM course_hole_handicap)
        ORDER BY handicap_rank ASC
    """)
    handicap_holes = [f"s.hole_{row[0]}" for row in cursor.fetchall()]
    order_by_clause = ", ".join(handicap_holes) if handicap_holes else f"s.{order_by_field}"

    query = f"""
        SELECT s.first_name, s.last_name, s.total, s.net_score, {order_by_clause}
        FROM scores s
        WHERE s.{order_by_field} > 0
    """

    # Exclude total winners from net rankings if specified
    if exclude_winners and winners:
        placeholders = ', '.join(['(%s, %s)'] * len(winners))
        winner_values = [val for pair in winners for val in pair]
        query += f"AND (s.first_name, s.last_name) NOT IN ({placeholders}) "
    else:
        winner_values = []

    query += f"ORDER BY s.{order_by_field} ASC, {order_by_clause} ASC LIMIT %s"
    params = winner_values + [top_n]

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [{"first_name": row[0], "last_name": row[1], "total_score": row[2], "net_score": row[3]} for row in results]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():
    if request.method == "POST":
        total_positions = int(request.form["total_positions"])
        net_positions = int(request.form["net_positions"])
    else:
        total_positions = 5
        net_positions = 5

    course_info = get_latest_course()
    total_results = fetch_ranked_results("total", top_n=total_positions)
    winners = set((p["first_name"], p["last_name"]) for p in total_results)
    net_results = fetch_ranked_results("net_score", exclude_winners=True, winners=winners, top_n=net_positions)

    return render_template(
        "leaderboard.html",
        course=course_info,
        total_results=total_results,
        net_results=net_results
    )

@app.route("/api/leaderboard")
def api_leaderboard():
    """Return leaderboard data in JSON format."""
    total_positions = request.args.get("total_positions", default=5, type=int)
    net_positions = request.args.get("net_positions", default=5, type=int)

    course_info = get_latest_course()
    total_results = fetch_ranked_results("total", top_n=total_positions)
    winners = set((p["first_name"], p["last_name"]) for p in total_results)
    net_results = fetch_ranked_results("net_score", exclude_winners=True, winners=winners, top_n=net_positions)

    return jsonify({
        "course_info": course_info,
        "total_results": total_results,
        "net_results": net_results
    })
