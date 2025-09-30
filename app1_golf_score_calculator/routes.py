from app1_golf_score_calculator.excel_cache import ExcelCache
from app1_golf_score_calculator.callaway_logic import calculate_callaway_score
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort, flash
from . import score_calc_bp
from datetime import datetime
import logging
from utils.course import extract_course_name_and_date
from utils.names import canonicalize_name
from utils.db import get_db_cursor, get_db_connection, mysql_connection, get_player_counts, insert_or_update_score
import subprocess
import sys
import os
import time
from dotenv import load_dotenv
import random
import traceback
import re
import mysql.connector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()
logger = logging.getLogger(__name__)
golf_bp = Blueprint('golf', __name__)

def get_submitted_count(ws):
    submitted = 0
    # Start at row 4, go through the last row
    for row in range(4, ws.max_row + 1):
        value = ws.cell(row=row, column=25).value  # Column Y is 25
        if value is not None and str(value).strip() != "":
            submitted = 1
    return submitted

def get_total_count(ws):
    total = 0
    # Start at row 4, go through the last row
    for row in range(4, ws.max_row + 1):
        value = ws.cell(row=row, column=1).value  # Column A = 1
        if value is not None and str(value).strip() != "":
            total = 1
    return total

def run_script(script_name, args=None):
    try:
        # Manually set the path to app2_golf_script_runner
        working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app2_golf_script_runner"))
        os.chdir(working_dir)

        script_path = os.path.join(working_dir, script_name)
        print(f"📁 Checking script at: {script_path}", flush=True)

        if not os.path.isfile(script_path):
            print(f"❌ Script not found: {script_path}", flush=True)
            return f"❌ Script not found: {script_path}"

        command = [sys.executable, script_path]
        if args:
            command.extend(args)

        print(f"🚀 Running command: {' '.join(command)}", flush=True)
        process = subprocess.run(command, check=False, text=True, capture_output=True)
        print(f"📤 STDOUT:\n{process.stdout[:300]}", flush=True)
        print(f"📥 STDERR:\n{process.stderr[:300]}", flush=True)
        return process.stdout

    except Exception as e:
        return f"❌ Error running {script_name}: {str(e)}"


# mysql_connection is now imported from utils.db


@score_calc_bp.route("/set_session", methods=["POST"])
def set_session():
    raw_name = request.form.get("course_name", "").strip()
    raw_date = request.form.get("course_date", "").strip()

    def is_bad_course_name(name):
        return (
            not name or
            "name" in name.lower() or
            any(c in name for c in "!@#$%^&*") or
            len(name) < 2
        )

    if is_bad_course_name(raw_name):
        print(f"⚠️ Rejected bad course name input: '{raw_name}'", flush=True)
        return "Invalid course name", 400

    if not raw_date:
        return "Missing course date", 400

    session["course_name"] = raw_name
    session["course_date"] = raw_date
    print(f"✅ Session set: course_name = {raw_name}, course_date = {raw_date}", flush=True)
    return "OK"

@score_calc_bp.route('/', strict_slashes=False)
def index():
    excel_path = ExcelCache.get_excel_path()
    course_name, course_date = "Current Tournament", ""

    # Use shared utility to get player counts
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(course_id),1) FROM courses")
        course_id = cursor.fetchone()[0]

    counts = get_player_counts(course_id)

    # Debug logging
    print(f"🔍 INDEX ROUTE - course_id: {course_id}")
    print(f"🔍 INDEX ROUTE - counts: {counts}")
    print(f"🔍 INDEX ROUTE - submitted_count: {counts['submitted_count']}")
    print(f"🔍 INDEX ROUTE - total_count: {counts['total_count']}")
    print(f"🔍 INDEX ROUTE - players_left: {counts['players_left']}")

    return render_template(
      "index.html",
      submitted_count=counts['submitted_count'],
      total_count=counts['total_count'],
      players_left=counts['players_left'],
      course_name=course_name,
      course_date=course_date,
      course_id=course_id
    )

@golf_bp.route('/callaway_results/')
def callaway_results():
    return render_template('landing.html')

@score_calc_bp.route('/get_course_name', methods=['GET'])
def get_course_name():
    return jsonify({
        "course_name": session.get("course_name", "Unknown"),
        "date": datetime.today().strftime("%B %d, %Y")
    })

@score_calc_bp.route("/admin_add_player", methods=["POST"])
def admin_add_player():
    data = request.get_json()
    first = data.get("first_name")
    last = data.get("last_name")
    if not first or not last:
        return jsonify(success=False, message="⚠️ First and last name required.")

    try:
        conn = mysql_connection()
        cursor = conn.cursor()

        # Get latest course_id
        cursor.execute("SELECT MAX(course_id) FROM courses")
        course_id = cursor.fetchone()[0] or 1

        # Check if player already exists for this course in players table
        cursor.execute("""
            SELECT 1 FROM players
            WHERE course_id = %s AND first_name = %s AND last_name = %s
        """, (course_id, first, last))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify(success=False, message=f"⚠️ {first} {last} already exists for this course.")

        # Insert into players table
        cursor.execute("""
            INSERT INTO players (first_name, last_name, course_id)
            VALUES (%s, %s, %s)
        """, (first, last, course_id))

        conn.commit()

        # Get updated counts after addition
        cursor.execute("SELECT COUNT(*) FROM players WHERE course_id = %s", (course_id,))
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scores WHERE total IS NOT NULL AND course_id = %s", (course_id,))
        submitted_count = cursor.fetchone()[0]

        # Refresh player list from players table
        cursor.execute("""
            SELECT CONCAT(first_name, ' ', last_name) AS full_name
            FROM players
            WHERE course_id = %s
            ORDER BY first_name, last_name
        """, (course_id,))
        players = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify(
            success=True,
            message=f"✅ Added {first} {last}",
            players=players,
            total_count=total_count,
            submitted_count=submitted_count,
            players_left=max(total_count - submitted_count, 0)
        )

    except Exception as e:
        return jsonify(success=False, message=f"❌ DB Error: {e}")

@score_calc_bp.route("/admin_remove_player", methods=["POST"])
def admin_remove_player():
    data = request.get_json()
    full_name = data.get("full_name")
    if not full_name:
        return jsonify(success=False, message="⚠️ No player name provided.")

    try:
        first, last = full_name.split(" ", 1)
    except ValueError:
        return jsonify(success=False, message="⚠️ Invalid player name format.")

    try:
        conn = mysql_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(course_id) FROM courses")
        course_id = cursor.fetchone()[0] or 1

        # Remove player for current course
        cursor.execute("""
            DELETE FROM scores
            WHERE course_id = %s AND first_name = %s AND last_name = %s
        """, (course_id, first, last))

        # Remove from players table too
        cursor.execute("""
            DELETE FROM players
            WHERE course_id = %s AND first_name = %s AND last_name = %s
        """, (course_id, first, last))

        conn.commit()

        # Get updated counts after removal
        cursor.execute("SELECT COUNT(*) FROM players WHERE course_id = %s", (course_id,))
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scores WHERE total IS NOT NULL AND course_id = %s", (course_id,))
        submitted_count = cursor.fetchone()[0]

        # Refresh player list from players table (not scores!)
        cursor.execute("""
            SELECT CONCAT(first_name, ' ', last_name) AS full_name
            FROM players
            WHERE course_id = %s
            ORDER BY first_name, last_name
        """, (course_id,))
        players = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify(
            success=True,
            message=f"🗑️ Removed {first} {last}",
            players=players,
            total_count=total_count,
            submitted_count=submitted_count,
            players_left=max(total_count - submitted_count, 0)
        )

    except Exception as e:
        return jsonify(success=False, message=f"❌ DB Error: {e}")

@score_calc_bp.route("/get_names", methods=["GET"])
def get_names():
    try:
        conn = mysql_connection()
        cursor = conn.cursor()

        # Get current course_id
        cursor.execute("SELECT COALESCE(MAX(course_id), 1) FROM courses")
        course_id = cursor.fetchone()[0]

        # Get full names by concatenating first_name and last_name
        cursor.execute("""
            SELECT CONCAT(first_name, ' ', last_name) AS full_name
            FROM players
            WHERE course_id = %s
            AND first_name IS NOT NULL
            AND last_name IS NOT NULL
            AND TRIM(first_name) != ''
            AND TRIM(last_name) != ''
            ORDER BY first_name, last_name
        """, (course_id,))

        results = cursor.fetchall()
        names = [row[0] for row in results if row[0] is not None]

        cursor.close()
        conn.close()
        print(f"✅ Returning {len(names)} full player names for course {course_id}")
        return jsonify(names)
    except Exception as e:
        print(f"❌ Error fetching names: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])
    

@score_calc_bp.route('/export_to_archive', methods=['POST'])
def export_to_archive():
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        # ✅ Insert scores with course_name and date_played
        cursor.execute("""
            INSERT INTO scores_archive (course_id, course_name, date_played, first_name, last_name, total, net_score, snapshot_id)
            SELECT s.course_id, c.course_name, c.date_played, s.first_name, s.last_name, s.total, s.net_score, NULL
            FROM scores s
            JOIN courses c ON s.course_id = c.course_id
        """)

        # ✅ Update any existing rows with NULL values (in case of older records)
        cursor.execute("""
            UPDATE scores_archive sa
            JOIN courses c ON sa.course_id = c.course_id
            SET sa.course_name = c.course_name,
                sa.date_played = c.date_played
            WHERE sa.course_name IS NULL OR sa.date_played IS NULL
        """)

        conn.commit()
        return jsonify({"success": True, "message": "✅ Scores exported with course name and date."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"❌ Export failed: {str(e)}"})
    finally:
        cursor.close()
        conn.close()



@score_calc_bp.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        course_id = data.get("course_id")
        total = data.get("total")
        holes = data.get("holes")

        if not holes or not isinstance(holes, list) or len(holes) != 18:
            return jsonify(success=False, message="Invalid or missing hole scores.")

        print("Received hole scores:", holes)

        first_name, last_name = canonicalize_name(first_name, last_name)  # ✅ PATCHED

        ws = ExcelCache.get_sheet()
        course_name = ws.cell(row=1, column=1).value or "Unknown Course"
        course_par = ExcelCache.get_par()
        if course_par is None:
            abort(500, description="❌ Course par not found in Excel; cannot submit scores.")

        print(f"✅ Loaded worksheet: {ws.title}")
        print(f"🧮 Inputs to Callaway: holes={holes}, course_par={course_par}")

        try:
            gross, deducted, adjustment, net_score = calculate_callaway_score(holes, course_par)
            print(f"📉 Net Score Calculated: {net_score}")
        except Exception as e:
            print("❌ Callaway calculation error:", e)
            return jsonify(success=False, message=f"Callaway logic failed: {str(e)}")

        conn = mysql_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT total FROM scores
            WHERE first_name = %s AND last_name = %s AND course_id = %s
        """, (first_name, last_name, course_id))
        result = cursor.fetchone()

        if result:
            print("♻️ Updating existing player scores.")
            update_query = """
                UPDATE scores
                SET
                    hole_1 = %s, hole_2 = %s, hole_3 = %s, hole_4 = %s, hole_5 = %s,
                    hole_6 = %s, hole_7 = %s, hole_8 = %s, hole_9 = %s,
                    hole_10 = %s, hole_11 = %s, hole_12 = %s, hole_13 = %s, hole_14 = %s,
                    hole_15 = %s, hole_16 = %s, hole_17 = %s, hole_18 = %s,
                    total = %s, net_score = %s
                WHERE first_name = %s AND last_name = %s AND course_id = %s
            """
            cursor.execute(update_query, (
                *holes, total, net_score, first_name, last_name, course_id
            ))
        else:
            print(f"➕ Inserting new score row for {first_name} {last_name} (Course ID: {course_id})")
            insert_query = """
                INSERT INTO scores (
                    first_name, last_name, course_id,
                    hole_1, hole_2, hole_3, hole_4, hole_5,
                    hole_6, hole_7, hole_8, hole_9,
                    hole_10, hole_11, hole_12, hole_13, hole_14,
                    hole_15, hole_16, hole_17, hole_18,
                    total, net_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                first_name, last_name, course_id,
                *holes, total, net_score
            ))

        cursor.execute("SELECT COUNT(*) FROM scores WHERE total IS NOT NULL AND course_id = %s", (course_id,))
        submitted_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM players WHERE course_id = %s", (course_id,))
        total_count = cursor.fetchone()[0]
        players_left = max(total_count - submitted_count, 0)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "✅ Score submitted.",
            "submitted_count": submitted_count,
            "total_count": total_count,
            "players_left": players_left
        })

    except Exception as e:
        print("❌ DB Error:", e)
        return jsonify(success=False, message=f"Database error: {str(e)}")

@score_calc_bp.route("/load_history")
def load_history():
    return render_template("historical_loader.html")

@score_calc_bp.route("/run_history_scripts", methods=["POST"])
def run_history_scripts():
    course_name = request.form.get("course_name")
    course_date = request.form.get("course_date")

    print(f"Loading historical data for {course_name} on {course_date}")
    return jsonify(progress=["Step 1", "Step 2", "Step 3"], logs=["History script started...", "Done."])

@score_calc_bp.route('/run_scripts', methods=['POST'])
def run_scripts():
    print("✅ /run_scripts route triggered", flush=True)
    data = request.get_json()
    course_name = data['course_name']
    course_date = data['course_date']

    print(f"📢 Calling convert_and_import_all.py with: {course_name}, {course_date}", flush=True)

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
        truncate_message = "✅ Fives table truncated successfully."
    except Exception as e:
        truncate_message = f"⚠️ Database error: {e}"

    output = run_script("convert_and_import_all.py")
    print(f"📥 Script output received:\n{output[:300]}...", flush=True)
    output_logs = [output.strip()]

    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_filename = f"tournament_log_{timestamp}.txt"
    log_path = os.path.join(log_dir, log_filename)

    with open(log_path, "w") as log_file:
        log_file.write("\n\n".join(output_logs))

    return jsonify({
        "message": truncate_message,
        "logs": output_logs,
        "progress": [],
        "log_path": f"/logs/{log_filename}"
    })

@score_calc_bp.route('/run_tournament_scripts_v2', methods=['POST'])
def run_tournament_scripts_v2():
    print("✅ /run_tournament_scripts_v2 route triggered", flush=True)

    try:
        runner_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app2_golf_script_runner"))
        os.chdir(runner_dir)
        runner_script = os.path.join(runner_dir, "convert_and_import_all_simplified.py")
        print(f"📁 Checking script at: {runner_script}", flush=True)

        result = subprocess.run(
            [sys.executable, runner_script],
            text=True,
            capture_output=True,
            check=False
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = f"📤 STDOUT:\n{stdout}\n📥 STDERR:\n{stderr}"
        print(f"📥 Script output received:\n{output}", flush=True)

        return output, 200
    except Exception as e:
        error_msg = f"❌ Error launching script: {e}"
        print(error_msg, flush=True)
        return error_msg, 500

@score_calc_bp.route('/logs/<path:filename>')
def download_log(filename):
    log_dir = os.path.join(os.getcwd(), "logs")
    return send_from_directory(log_dir, filename, as_attachment=True)

@score_calc_bp.route('/score', methods=['POST'])
def score():
    try:
        data = request.get_json()
        scores = data.get("scores")
        course_par = data.get("course_par", 72)  # Optional override

        if not scores or len(scores) != 18:
            return jsonify({"error": "Exactly 18 scores required"}), 400

        gross, deducted, adjustment, net = calculate_callaway_score(scores, course_par=course_par)
        return jsonify({
            "gross": gross,
            "deducted": deducted,
            "adjustment": adjustment,
            "net": net
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@score_calc_bp.route('/reset_scores', methods=['POST'])
def reset_scores():
    try:
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Clear all rows from the scores table
        cursor.execute("DELETE FROM scores")
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True, message="Scores cleared.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500

@score_calc_bp.route('/clear_fives', methods=['POST'])
def clear_fives():
    try:
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Clear all rows from the fives table
        cursor.execute("DELETE FROM fives")
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True, message="Fives table cleared.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500
    
@score_calc_bp.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    def normalize(name):
        return ''.join((name or '').lower().split())

    def canonicalize_name(first, last):
        full = f"{first.strip()} {last.strip()}"
        if full.lower() == "d j patterson":
            return "DJ", last
        if full == "mike a carroll":
            return "mikea", "carroll"
        if full == "mike p carroll":
            return "mikep", "carroll"
        return first.strip().lower(), last.strip().lower()

    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, last_name,
                hole_1, hole_2, hole_3, hole_4, hole_5, hole_6,
                hole_7, hole_8, hole_9, hole_10, hole_11, hole_12,
                hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                total, net_score
            FROM scores
        """)
        rows = cursor.fetchall()

        wb = ExcelCache.get_workbook()
        sheet = ExcelCache.get_sheet()

        # 🟩 Read range A4:B153 (rows 4-153, columns 1-2)
        name_range = [
            [cell.value for cell in row]
            for row in sheet.iter_rows(min_row=4, max_row=153, min_col=1, max_col=2)
        ]

        matched_count = 0
        unmatched = []

        for db_row in rows:
            db_first, db_last = canonicalize_name(db_row[0], db_row[1])
            db_canon = normalize(f"{db_first} {db_last}")
            match_found = False

            for i, row in enumerate(name_range, start=4):
                xl_canon = normalize(f"{row[0]} {row[1]}")
                if db_canon == xl_canon:
                    # 🟩 Write scores (columns D to V = 4 to 22)
                    for col_offset, score in enumerate(db_row[2:21], start=4):  # 2:21 = 19 scores
                        sheet.cell(row=i, column=col_offset).value = score

                    # 🟩 Write net_score in column T (46)
                    sheet.cell(row=i, column=46).value = db_row[21]

                    matched_count = 1
                    match_found = True
                    break

            if not match_found:
                unmatched.append(f"{db_row[0]} {db_row[1]}")

        wb.save(ExcelCache.loaded_path)
        print(f"✅ Exported {matched_count} players. Unmatched: {len(unmatched)}")
        if unmatched:
            print("❗ Unmatched entries:", unmatched)

        return jsonify(success=True, message=f"✅ Export complete. Matched: {matched_count}, Unmatched: {len(unmatched)}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f"❌ Export failed: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@score_calc_bp.route('/debug_players', methods=['GET'])
def debug_players():
    try:
        conn = mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players")
        players = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({
            "count": len(players),
            "players": players
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        })

@score_calc_bp.route('/check_table_schema', methods=['GET'])
def check_table_schema():
    try:
        conn = mysql_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Get structure of players table
        cursor.execute("DESCRIBE players")
        schema = [{"Field": row[0], "Type": row[1], "Null": row[2], "Key": row[3]} 
                 for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "tables": tables,
            "players_schema": schema
        })
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

def is_valid_player_name(first, last):
    """
    Check if a name pair represents a real player (not headers or placeholders).
    Returns True for valid players, False for invalid ones.
    """
    if not first or not last:
        return False
        
    # Convert to strings and clean
    first = str(first).strip().lower()
    last = str(last).strip().lower()
    
    # Check for empty values
    if not first or not last:
        return False
        
    # Check for headers
    if first in ["first", "first name"] or last in ["last", "last name"]:
        return False
        
    # Check for placeholders (e.g., "Xxxxxxxx")
    if re.match(r'^x+$', first, re.IGNORECASE) or re.match(r'^x+$', last, re.IGNORECASE):
        return False
    
    # Check for numeric values
    if first.isdigit() or last.isdigit():
        return False
    
    # Check for common placeholder values
    placeholders = ['none', 'null', 'na', 'n/a', 'blank', 'unknown', 'test']
    if first in placeholders or last in placeholders:
        return False
        
    return True

@golf_bp.route('/simulate_round', methods=['POST'])
def simulate_round():
    try:
        # Get course info
        course_id = request.form.get('course_id') or session.get('course_id')
        if not course_id:
            return jsonify({"success": False, "error": "No course_id provided"})
        
        # Connect to database
        conn = mysql_connection()
        cursor = conn.cursor()
        
        # Get players from database
        cursor.execute("SELECT DISTINCT first_name, last_name FROM players")
        players = cursor.fetchall()
        print(f"Found {len(players)} players in database")
        
        # Filter out invalid players
        valid_players = []
        skipped_players = []
        
        for player in players:
            first_name, last_name = player
            if is_valid_player_name(first_name, last_name):
                valid_players.append(player)
            else:
                skipped_players.append(f"{first_name} {last_name}")
                print(f"Skipping invalid player: {first_name} {last_name}")
        
        print(f"Filtered {len(players)} players to {len(valid_players)} valid players")
        
        # Generate and insert random scores for valid players
        scores_inserted = 0
        for first_name, last_name in valid_players:
            # Generate random scores between 3 and 8 for each hole
            scores = [random.randint(3, 8) for _ in range(18)]
            total = sum(scores)
            
            # Check if player already exists
            cursor.execute("""
                SELECT 1 FROM scores 
                WHERE first_name = %s AND last_name = %s AND course_id = %s
            """, (first_name, last_name, course_id))
            
            if cursor.fetchone():
                # Update existing record
                update_query = """
                    UPDATE scores SET 
                        hole_1=%s, hole_2=%s, hole_3=%s, hole_4=%s, hole_5=%s,
                        hole_6=%s, hole_7=%s, hole_8=%s, hole_9=%s,
                        hole_10=%s, hole_11=%s, hole_12=%s, hole_13=%s, hole_14=%s,
                        hole_15=%s, hole_16=%s, hole_17=%s, hole_18=%s,
                        total=%s
                    WHERE first_name=%s AND last_name=%s AND course_id=%s
                """
                cursor.execute(update_query, (*scores, total, first_name, last_name, course_id))
            else:
                # Insert new record
                insert_query = """
                    INSERT INTO scores (
                        first_name, last_name, course_id,
                        hole_1, hole_2, hole_3, hole_4, hole_5, hole_6, hole_7, hole_8, hole_9,
                        hole_10, hole_11, hole_12, hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                        total
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (first_name, last_name, course_id, *scores, total))
            
            scores_inserted += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Simulated scores for {scores_inserted} players",
            "skipped": skipped_players
        })
        
    except Exception as e:
        print(f"Error in simulate_round: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@score_calc_bp.route("/ensure_all_scores", methods=["POST"])
def ensure_all_scores():
    """Make sure all players have scores after simulation"""
    import random
    import pymysql
    from flask import current_app
    
    try:
        # Get database connection
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # Get latest course_id (default to 2 if not found)
        cursor.execute("SELECT MAX(course_id) FROM scores")
        course_id_result = cursor.fetchone()
        course_id = course_id_result[0] if course_id_result and course_id_result[0] else 2
        
        # Find players without scores - improved logic
        cursor.execute("""
            SELECT p.first_name, p.last_name FROM players p
            WHERE p.course_id = %s AND NOT EXISTS (
                SELECT 1 FROM scores s 
                WHERE s.first_name = p.first_name 
                AND s.last_name = p.last_name 
                AND s.course_id = %s
            )
        """, [course_id, course_id])
        
        missing = cursor.fetchall()
        fixed_count = 0
        
        for row in missing:
            first_name, last_name = row
            print(f"⚠️ Adding missing scores for {first_name} {last_name}")
            
            # Generate random scores between 2-8 for each hole
            hole_scores = [random.randint(2, 8) for _ in range(18)]
            out_score = sum(hole_scores[:9])
            in_score = sum(hole_scores[9:])
            total_score = out_score + in_score
            
            # Insert scores
            try:
                cursor.execute("""
                    INSERT INTO scores (
                        first_name, last_name, course_id,
                        hole_1, hole_2, hole_3, hole_4, hole_5, hole_6, hole_7, hole_8, hole_9,
                        hole_10, hole_11, hole_12, hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                        total, net_score
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                """, [
                    first_name, last_name, course_id, 
                    hole_scores[0], hole_scores[1], hole_scores[2], hole_scores[3], 
                    hole_scores[4], hole_scores[5], hole_scores[6], hole_scores[7], 
                    hole_scores[8], hole_scores[9], hole_scores[10], hole_scores[11], 
                    hole_scores[12], hole_scores[13], hole_scores[14], hole_scores[15], 
                    hole_scores[16], hole_scores[17],
                    total_score, total_score  # Using total as net_score for now
                ])
                fixed_count += 1
                print(f"✅ Added scores for {first_name} {last_name}")
            except Exception as e:
                print(f"❌ Error adding scores: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Fixed {fixed_count} missing players",
            "fixed_count": fixed_count
        })
        
    except Exception as e:
        print(f"Error in ensure_all_scores: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@score_calc_bp.route('/get_counts', methods=['GET'])
def get_counts():
    """Get current count statistics for the scorecard display"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(course_id),1) FROM courses")
            course_id = cursor.fetchone()[0]

        counts = get_player_counts(course_id)

        print(f"🔍 GET_COUNTS - course_id: {course_id}")
        print(f"🔍 GET_COUNTS - counts: {counts}")

        result = {
            "submitted": counts['submitted_count'],
            "total": counts['total_count'],
            "left": counts['players_left']
        }

        print(f"🔍 GET_COUNTS - returning: {result}")

        return jsonify(result)

    except Exception as e:
        print(f"❌ GET_COUNTS ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
