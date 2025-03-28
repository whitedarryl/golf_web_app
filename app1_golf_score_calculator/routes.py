import csv
import win32com.client
import os
import glob
from datetime import datetime
from flask import render_template, jsonify, request
import pythoncom
from . import score_calc_bp
from .logic import extract_names_from_excel, extract_course_name_and_today, get_available_players, get_total_players, get_submitted_player_count, reset_excel_cache

@score_calc_bp.route("/")
def index():
    course_name, course_date = extract_course_name_and_today()
    players = get_available_players()
    return render_template("score_calc/index.html",
                           course_name=course_name,
                           course_date=course_date,
                           players=players)

@score_calc_bp.route("/get_names")
def get_names():
    try:
        names = get_available_players()
        total = get_total_players()
        submitted = get_submitted_player_count()  # 🔥 NEW
        return jsonify(success=True, names=names, total=total, submitted=submitted)
    except Exception as e:
        import traceback
        print("❌ Error in /get_names:", e)
        traceback.print_exc()
        return jsonify(success=False, message=str(e)), 500

@score_calc_bp.route("/submit", methods=["POST"])
def submit_score():
    try:
        print("🔄 /submit route hit")
        data = request.get_json()
        full_name = data.get("name", "").strip()
        scores = data.get("scores", [])
        out = data.get("out")
        inn = data.get("inn")
        total = data.get("total")

        if not full_name or len(scores) != 18:
            return jsonify(success=False, message="Invalid submission.")

        first, last = full_name.split(" ", 1)

        # Load Excel file
        folder = os.getenv("GOLF_WEBAPP_FOLDER", "C:\\Golf Web App_backup")
        pattern = os.path.join(folder, "*Callaway scoring sheet.xls")
        matches = glob.glob(pattern)
        if not matches:
            return jsonify(success=False, message="Callaway Excel file not found.")

        excel_path = matches[0]
        pythoncom.CoInitialize()
        excel = win32com.client.Dispatch("Excel.Application")
        wb = excel.Workbooks.Open(excel_path)
        sheet = wb.Worksheets("Scores")

        # Find the matching row
        found_row = None
        for i in range(4, 200):  # Increase range just in case
            f = sheet.Cells(i, 1).Value
            l = sheet.Cells(i, 2).Value
            print(f"Checking row {i}: |{f}| |{l}| vs input |{first}| |{last}|")
            if f and l:
                full_excel = ' '.join(f"{f} {l}".split()).strip().lower()
                full_input = ' '.join(full_name.split()).strip().lower()
                if full_excel == full_input:
                    found_row = i
                    break

        if not found_row:
            wb.Close(SaveChanges=0)
            excel.Quit()
            return jsonify(success=False, message="Player not found in Excel sheet.")

        # Write scores to Excel
        for idx, score in enumerate(scores):
            col = 4 + idx
            sheet.Cells(found_row, col).Value = score

        wb.Save()
        wb.Close(SaveChanges=0)
        excel.Quit()

        reset_excel_cache()

        # Also write to archive CSV
        safe_course = extract_course_name_and_today()[0].replace(" ", "_").lower()
        archive_dir = os.path.join(folder, "score_archive")
        os.makedirs(archive_dir, exist_ok=True)
        archive_file = os.path.join(archive_dir, f"{safe_course}_scores.csv")

        row = [' '.join(full_name.split()).strip()] + scores + [out, inn, total]

        if not os.path.exists(archive_file):
            with open(archive_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Name"] + [f"Hole {i}" for i in range(1, 19)] + ["Out", "In", "Total"])
                writer.writerow(row)
        else:
            with open(archive_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        print("✅ Score written to archive for:", full_name)
        return jsonify(success=True)

    except Exception as e:
        import traceback
        print("❌ Error in /submit:", e)
        traceback.print_exc()
        return jsonify(success=False, message="Something went wrong."), 500

@score_calc_bp.route("/archive")
def view_archive():
    course_name, _ = extract_course_name_and_today()
    safe_course = course_name.replace(" ", "_").lower()
    archive_dir = os.path.join(os.getenv("GOLF_WEBAPP_FOLDER", "C:\\Golf Web App_backup"), "score_archive")
    filename = os.path.join(archive_dir, f"{safe_course}_scores.csv")

    rows = []
    headers = []
    if os.path.exists(filename):
        with open(filename, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            rows = list(reader)

    return render_template("score_calc/archive.html", headers=headers, rows=rows, course=course_name)
