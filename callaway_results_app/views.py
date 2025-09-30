from flask import Blueprint, render_template, request, redirect, url_for
from dotenv import load_dotenv
from markupsafe import Markup
from .utils import get_latest_course
from collections import defaultdict
from .callaway import calculate_callaway_score
from utils.db import get_db_cursor, get_db_connection


print("✅ views.py is loaded")

load_dotenv()

callaway_app = Blueprint(
    "callaway_results",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)


def fetch_ranked_results(order_by_field, exclude_winners=False, winners=None, top_n=5):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hole_number FROM course_hole_handicap
            WHERE course_id = (SELECT MAX(course_id) FROM course_hole_handicap)
            ORDER BY handicap_rank ASC
        """)
        hole_rows = cursor.fetchall()
        handicap_holes = [f"s.hole_{row[0]}" for row in hole_rows]
        print("🧩 Handicap holes used for ordering:", handicap_holes)

        order_by_clause = ", ".join(handicap_holes) if handicap_holes else f"s.{order_by_field}"
        print("🧠 ORDER BY clause:", order_by_clause)

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

        print("📤 Executing SQL query:")
        print(query)
        print("📦 Params:", params)

        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()

        print(f"✅ Query returned {len(results)} results.")
        if results:
            print("🔍 Sample row:", results[0])

        return [
            {"first_name": row[0], "last_name": row[1], "total_score": row[2], "net_score": row[3]}
            for row in results
        ]


@callaway_app.route("/", methods=["GET"])
def index():
    try:
        course_info = get_latest_course()
        
        return render_template(
            "landing.html",
            course=course_info['course_name'],
            date=course_info["date_played"])
    except Exception as e:
        return f"❌ Error rendering landing page: {e}", 500


@callaway_app.route("/leaderboard", methods=["POST"])
def leaderboard():
    try:
        total_positions = int(request.form["total_positions"])
        net_positions = int(request.form["net_positions"])

        course_info = get_latest_course()
        total_results = fetch_ranked_results("total", top_n=total_positions)
        winners = set((p["first_name"], p["last_name"]) for p in total_results)
        net_results = fetch_ranked_results("net_score", exclude_winners=True, winners=winners, top_n=net_positions)

        return render_template(
            "leaderboard.html",
            course=course_info['course_name'],
            date=course_info["date_played"],
            total_results=total_results,
            net_results=net_results,
            total_tiebreaks=add_tiebreak_ranks(total_results, key='total_score'),
            net_tiebreaks=add_tiebreak_ranks(net_results, key='net_score')
        )

    except Exception as e:
        return f"❌ Error rendering leaderboard: {e}", 500


@callaway_app.route("/dev/callaway", methods=["POST"])
def callaway_dev_score():
    from .callaway import calculate_callaway_score
    data = request.json
    scores = data.get("scores")

    if not scores or len(scores) != 18:
        return {"error": "Must provide exactly 18 hole scores"}, 400

    print("▶️ Scoring:", scores)
    
    try:
        gross, deducted, adjustment, net = calculate_callaway_score(scores)
        print("📤 Gross:", gross, "Deducted:", deducted, "Adj:", adjustment, "Net:", net)
        return {
            "gross": gross,
            "deducted": deducted,
            "adjustment": adjustment,
            "net": net
        }
    except Exception as e:
        print("🔥 ERROR:", e)
        return {"error": str(e)}, 500
    

def add_tiebreak_ranks(players, key="net_score"):
    tie_groups = defaultdict(list)
    for p in players:
        tie_groups[p[key]].append(p)

    ranked = {}
    for score, group in tie_groups.items():
        if len(group) > 1:
            for idx, p in enumerate(group):
                ranked[(p['first_name'], p['last_name'])] = idx + 1
    return ranked