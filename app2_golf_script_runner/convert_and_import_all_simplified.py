
import os, sys, subprocess
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime
import re

def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

# Load DB config
load_dotenv()
db_config = {
    "host":     os.getenv("DB_HOST"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# Import course manager to get current course_id dynamically
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db import get_latest_course_id

# Get current course_id dynamically
course_id = get_latest_course_id()

def extract_course_prefix_from_filename(fname):
    """Extract the sheet name part like 'Deerfield 7-26-25' from the Excel filename."""
    name_no_ext = fname.replace('.xlsx', '')
    parts = name_no_ext.split(')')
    if len(parts) > 1:
        course_name = parts[1].strip()
    else:
        course_name = name_no_ext.strip()
    
    # 🔥 Remove any trailing "-1", "-2", etc.
    course_name = re.sub(r'\s*-\d+$', '', course_name)
    return course_name

# helper to print score counts
def print_score_count(label):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scores")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"[OK] [{label}] Score rows count: {count}", flush=True)
    except Exception as e:
        print(f"[X] Error checking score count ({label}): {e}", flush=True)

# Clear fives table
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE fives;")
    conn.commit()
    cursor.close()
    conn.close()
    log("Fives table truncated successfully.")
except Exception as e:
    print(f"Database error: {e}", flush=True)

log(">>> Starting script run")

scripts = [
    "convert_xlsx_to_csv.py",
    "convert_xlsx_to_csv_handicap_ranks.py",
    "extract_handicap_order.py",
    "import_golf_scores.py",
    "archive_scores_snapshot.py",
    "import_handicap_ranks.py",
    "fives_import.py"
]

def summarize(output):
    if not output:
        return "(no output)"
    lines = output.splitlines()
    return "\n".join(
        l for l in lines
        if any(k in l.lower() for k in ["started", "import", "success", "error", "invalid", "completed", "inserted", "fetched"])
        and not l.strip().startswith("Columns found")
    )

open("run_log.txt", "w").close()

for script in scripts:
    print_score_count(f"BEFORE {script}")
    print(f">> Running {script}", flush=True)

    args = [sys.executable, script]

    if script == "import_golf_scores.py":
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "golf_scores.csv"))
        args.extend([str(course_id), csv_path])
    elif script == "archive_scores_snapshot.py":
        args.extend(["FixedCourse", "2025-07-01"])
    elif script == "import_handicap_ranks.py":
        args.extend(["FixedCourse", "2025-07-01"])
    elif script == "fives_import.py":
        import openpyxl
        base_dir = "C:\\Golf Web App Clone"
        xlsx_file = next(
            (f for f in os.listdir(base_dir)
            if f.lower().startswith("five five five") and f.lower().endswith(".xlsx")
            and not f.startswith("~$")),  # ignore temporary Excel files
            None
        )

        if xlsx_file:
            xlsx_path = os.path.join(base_dir, xlsx_file)
            log(f"Using Excel file for detection: {xlsx_path}")

            # ✅ Extract course prefix dynamically
            course_prefix = extract_course_prefix_from_filename(xlsx_file)
            args.extend([course_prefix, str(course_id)])

            wb = openpyxl.load_workbook(xlsx_path, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()

            # find the matching sheet if exists
            matching_sheets = [s for s in sheet_names if course_prefix.lower() in s.lower()]
            if matching_sheets:
                log(f"Matched sheet dynamically: {matching_sheets[0]}")
                args.extend([matching_sheets[0], str(course_id)])
            else:
                log("No exact sheet match found, defaulting to latest dated sheet.")
                args.extend([course_prefix, str(course_id)])
        else:
            log("No .xlsx file found in root.")
            args.extend(["FallbackSheet", str(course_id)])

    try:
        result = subprocess.run(
            args,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False
        )
        log(f"{script} exited with code {result.returncode}")
        if result.returncode != 0:
            log(f"--- {script} STDOUT ---\n{result.stdout or '(none)'}")
            log(f"--- {script} STDERR ---\n{result.stderr or '(none)'}")
        else:
            summary = "\n".join(
                l for l in (result.stdout or "").splitlines()
                if any(w in l.lower() for w in ("ok", "success", "inserted", "truncated"))
            )
            log(f"? {script} summary:\n{summary or '(no key messages)'}")

        print_score_count(f"AFTER {script}")
    except Exception as e:
        log(f"?? Failed to launch {script}: {e}")

log("All done.")
