from flask import Blueprint, render_template, request, jsonify, session
from .excel_cache import ExcelCache
from datetime import datetime

routes = Blueprint('routes', __name__, template_folder='templates', static_folder='static')

@routes.route('/')
def index():
    wb = ExcelCache.get_workbook()
    ws = wb.Sheets(1)

    submitted_count = 0
    total_count = 0

    for row in range(4, 200):
        name = ws.Cells(row, 2).Value
        if not name:
            break
        total_count += 1
        if ws.Cells(row, 25).Value:  # column Y = OUT score
            submitted_count += 1

    players_left = total_count - submitted_count

    return render_template(
        "index.html",
        submitted_count=submitted_count,
        total_count=total_count,
        players_left=players_left,
        course_name=session.get("course_name", "Unknown"),
        course_date=datetime.today().strftime("%B %d, %Y")
    )

@routes.route('/get_course_name', methods=['GET'])
def get_course_name():
    return jsonify({
        "course_name": session.get("course_name", "Unknown"),
        "date": datetime.today().strftime("%B %d, %Y")
    })

@routes.route("/get_names")
def get_names():
    try:
        sheet = ExcelCache.get_sheet()
        name_data = sheet.Range("A4:B153").Value

        all_names = []
        submitted_names = []

        for row in name_data:
            first, last = row
            if first and last:
                full_name = f"{first} {last}"
                all_names.append(full_name)

        # Get submitted players using your existing method
        submitted_names = ExcelCache.get_submitted_players(sheet)  # Ensure this returns names

        return jsonify({
            "success": True,
            "names": all_names,
            "submitted_names": submitted_names,
            "submitted": len(submitted_names),
            "total": len(all_names)
        })

    except Exception as e:
        print(f"❌ Error in /get_names: {e}")
        return jsonify(success=False, message="Failed to fetch names"), 500

@routes.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        full_name = data["name"]
        scores = data["scores"]
        out = data["out"]
        inn = data["inn"]
        total = data["total"]

        print("🔄 /submit route hit")

        wb = ExcelCache.get_workbook()
        ws = wb.Sheets(1)

        for row in range(4, 200):
            first = str(ws.Cells(row, 2).Value).strip()
            last = str(ws.Cells(row, 3).Value).strip()
            sheet_name = f"{first} {last}".strip()

            print(f"Checking row {row}: |{first}| |{last}| vs input |{full_name}|")

            if sheet_name.lower() == full_name.lower():
                for i in range(18):
                    ws.Cells(row, 6 + i).Value = scores.get(str(i + 1), 0)
                ws.Cells(row, 25).Value = out
                ws.Cells(row, 26).Value = inn
                ws.Cells(row, 27).Value = total
                ws.Cells(row, 28).Value = datetime.now().strftime("%m/%d/%Y %H:%M")
                break
        else:
            return jsonify(success=False, message="⚠️ Player not found in Excel sheet."), 404

        ExcelCache.refresh_cache()
        return jsonify(success=True, message=f"✅ Score submitted for: {full_name}")

    except Exception as e:
        print(f"🚨 Exception in /submit: {e}")
        return jsonify(success=False, message="❌ Failed to submit score."), 500
