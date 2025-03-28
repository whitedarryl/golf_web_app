import os
import glob
import pythoncom
import win32com.client
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GOLF_FOLDER = os.getenv("GOLF_FOLDER", "C:\\Golf")

def find_callaway_excel():
    """Find the most recent Callaway Excel file in the Golf folder."""
    files = glob.glob(os.path.join(GOLF_FOLDER, "*Callaway*.xls*"))
    if not files:
        raise FileNotFoundError("No Callaway Excel file found in Golf folder.")
    return max(files, key=os.path.getctime)

def extract_names_from_excel(file_path):
    """Open Excel and pull golfer names from specific sheet."""
    pythoncom.CoInitialize()
    excel = win32com.client.Dispatch("Excel.Application")
    wb = None
    try:
        wb = excel.Workbooks.Open(file_path)
        sheet = wb.Worksheets("Team Callaway")
        names = []

        for i in range(8, 72):
            val = sheet.Cells(i, 2).Value
            if val:
                names.append(val)
        return names
    finally:
        if wb:
            wb.Close(SaveChanges=0)
        excel.Quit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_names")
def get_names():
    try:
        excel_file = find_callaway_excel()
        names = extract_names_from_excel(excel_file)
        return jsonify(success=True, names=names)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True)
