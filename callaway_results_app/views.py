from flask import Blueprint, render_template, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv
import pdfkit
from flask import make_response
import re

load_dotenv()

callaway_app = Blueprint(
    'callaway_results',
    __name__,
    template_folder='templates',
    static_folder='static'
)

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

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
        return {
            "course_name": result[0],
            "date_played": result[1].strftime("%Y-%m-%d")
        }
    return {"course_name": "Unknown", "date_played": "0000-00-00"}

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

    return [
        {"first_name": row[0], "last_name": row[1], "total_score": row[2], "net_score": row[3]}
        for row in results
    ]

@callaway_app.route("/leaderboard/pdf", methods=["POST"])
def leaderboard_pdf():
    total_positions = int(request.form.get("total_positions", 5))
    net_positions = int(request.form.get("net_positions", 5))

    # ⬇️ Pull the same course info and results
    course_info = get_latest_course()
    total_results = fetch_ranked_results("total", top_n=total_positions)
    winners = set((p["first_name"], p["last_name"]) for p in total_results)
    net_results = fetch_ranked_results("net_score", exclude_winners=True, winners=winners, top_n=net_positions)

    rendered = render_template("leaderboard_pdf.html",
                               course=course_info,
                               total_results=total_results,
                               net_results=net_results)

    # ⬇️ Auto-generate dynamic filename
    safe_course = re.sub(r'\W+', '_', course_info["course_name"])
    date = course_info["date_played"]
    filename = f"leaderboard_{safe_course}_{date}.pdf"

    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # 👈 adjust as needed
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    # Save a copy
    save_path = os.path.join("exports", filename)
    os.makedirs("exports", exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(pdf)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@callaway_app.route("/", methods=["GET"])
def index():
    return render_template("landing.html")

@callaway_app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():
    try:
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
    except Exception as e:
        return f"❌ Error rendering leaderboard: {e}", 500

@callaway_app.route("/api/leaderboard", methods=["GET"])
def api_leaderboard():
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
