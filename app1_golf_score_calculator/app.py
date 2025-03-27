import win32com.client
import os
import glob
import pythoncom
import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="templates", static_folder="static")

def get_golf_course_name():
    excel_files = glob.glob(r"C:\Golf\*Callaway*.xls*")
    
    if not excel_files:
        print("❌ No Excel file found in C:\\Golf")
        return "Unknown Course"

    excel_file = os.path.basename(excel_files[0])
    print(f"📄 Found Excel File: {excel_file}")  # Debugging log

    parts = excel_file.split()
    course_name = []

    for part in parts:
        if part.isdigit():
            break
        course_name.append(part)

    course_name_str = " ".join(course_name)
    print(f"✅ Extracted Course Name: {course_name_str}")  # Debugging log

    return course_name_str

@app.route("/")
def index():
    golf_course = get_golf_course_name()
    print(f"✅ Golf Course Name: {golf_course}")  # Debugging print statement
    return render_template("index.html", golf_course=golf_course)

# ✅ Fetch player names from the Excel file
@app.route("/api/players", methods=["GET"])
def get_players():
    try:
        pythoncom.CoInitialize()  # Required for COM objects in Flask

        # ✅ Locate the Callaway Excel file
        excel_files = glob.glob(r"C:\Golf\*Callaway*.xls*")
        if not excel_files:
            return jsonify({"error": "No Callaway file found in C:\\Golf"}), 400

        excel_file_path = excel_files[0]
        print(f"✅ Found Excel file: {excel_file_path}")

        try:
            excel = win32com.client.Dispatch("Excel.Application")
        except Exception as e:
            print(f"❌ Excel Dispatch Error: {e}")
            return jsonify({"error": "Could not start Excel. Try running Flask as Administrator."}), 500

        try:
            wb = excel.Workbooks.Open(excel_file_path)
        except Exception as e:
            print(f"❌ Error Opening Workbook: {e}")
            return jsonify({"error": f"Error opening workbook: {e}"}), 500

        sheet = wb.Sheets("Scores")
        players_without_scores = []

        # ✅ Check each row for missing scores
        for row in range(3, sheet.UsedRange.Rows.Count + 1):
            first_name = (sheet.Cells(row, 1).Value or "").strip()
            last_name = (sheet.Cells(row, 2).Value or "").strip()
            full_name = f"{first_name} {last_name}".strip()

            # ✅ Get scores from Front 9 and Back 9
            front9_scores = [sheet.Cells(row, col).Value for col in range(3, 12)]
            back9_scores = [sheet.Cells(row, col).Value for col in range(12, 21)]

            # ✅ If ALL scores are empty or 0, include this player
            if all(score is None or score == 0 for score in front9_scores + back9_scores):
                players_without_scores.append(full_name)

        wb.Close(False)
        excel.Quit()

        return jsonify(players_without_scores)

    except Exception as e:
        print(f"❌ Error loading players: {e}")
        return jsonify({"error": f"Error loading players: {e}"}), 500

@app.route("/api/submit_scores", methods=["POST"])
def submit_scores():
    try:
        data = request.json
        full_name = data.get("player")
        front_9_scores = data.get("front_9")
        back_9_scores = data.get("back_9")

        if not full_name or not front_9_scores or not back_9_scores:
            return jsonify({"error": "Missing data"}), 400

        # Split full name into first and last names
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        pythoncom.CoInitialize()

        # ✅ Search for an Excel file in C:\Golf that contains "Callaway"
        excel_files = glob.glob(r"C:\Golf\*Callaway*.xls*")
        if not excel_files:
            return jsonify({"error": "No Callaway file found in C:\\Golf"}), 400

        excel_file_path = excel_files[0]
        print(f"✅ Found Excel file: {excel_file_path}")

        try:
            # ✅ Attach to already open Excel session
            excel = win32com.client.GetActiveObject("Excel.Application")
            wb = excel.Workbooks("Deerfield Black Friday 2024 Callaway scoring sheet.xls")
        except:
            # ✅ If Excel isn't open, open the file
            excel = win32com.client.Dispatch("Excel.Application")
            wb = excel.Workbooks.Open(excel_file_path)

        sheet = wb.Sheets("Scores")

        # ✅ Find the player row
        player_row = None
        for row in range(3, sheet.UsedRange.Rows.Count + 1):
            excel_first = (sheet.Cells(row, 1).Value or "").strip()
            excel_last = (sheet.Cells(row, 2).Value or "").strip()
            full_excel_name = f"{excel_first} {excel_last}".strip()

            if full_name.lower() == full_excel_name.lower():
                player_row = row
                break

        if player_row is None:
            return jsonify({"error": f"Player {full_name} not found in sheet."}), 400

        print(f"✅ Found player '{full_name}' at row {player_row}")

        # ✅ Save Front 9 Scores (Columns D-L, Excel Columns 4-12)
        for i in range(9):
            sheet.Cells(player_row, 4 + i).Value = front_9_scores[i]

        # ✅ Save Back 9 Scores (Columns M-U, Excel Columns 13-21)
        for i in range(9):
            sheet.Cells(player_row, 13 + i).Value = back_9_scores[i]

        # ✅ Disable pop-ups & Save
        excel.DisplayAlerts = False
        wb.Save()
        excel.DisplayAlerts = True

        print(f"✅ Scores successfully saved for {full_name}")

        return jsonify({"message": "Scores successfully saved to Excel!"})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": f"Error saving scores: {e}"}), 500

    finally:
        try:
            wb.Close(False)
            excel.Quit()
            print("✅ Excel file closed successfully")
        except Exception as close_error:
            print(f"⚠️ Warning: Issue closing Excel - {close_error}")

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
