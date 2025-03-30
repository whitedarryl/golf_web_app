import os
import glob
import re
import pythoncom
import win32com.client
from datetime import datetime
from dotenv import load_dotenv
from .excel_cache import ExcelCache

cache = ExcelCache()
load_dotenv()

# Define base folder
GOLF_FOLDER = os.getenv("GOLF_WEBAPP_FOLDER", "C:\\Golf Web App_backup")

def extract_course_name_from_file():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    pattern = r"^([\w\s]+?)\s+\w+\s+\d{4}\s+Callaway scoring sheet\.xls$"

    for filename in os.listdir(root_dir):
        match = re.match(pattern, filename)
        if match:
            return match.group(1).strip()

    return "Unknown"

def extract_course_name_and_today():
    pattern = os.path.join(GOLF_FOLDER, "*Callaway scoring sheet.xls")
    files = glob.glob(pattern)

    if not files:
        return ("Unknown Course", datetime.today().strftime("%B %d, %Y"))

    latest = max(files, key=os.path.getctime)
    filename = os.path.basename(latest)

    match = re.match(r"(.+?)\s+(January|February|March|April|May|June|July|August|September|October|November|December)", filename)
    if match:
        course = match.group(1).strip()
    else:
        course = "Unnamed Course"

    today = datetime.today().strftime("%B %d, %Y")
    return (course, today)


def get_total_players():
    return cache.get_total_players()

def extract_names_from_excel(file_path):
    pythoncom.CoInitialize()
    excel = win32com.client.Dispatch("Excel.Application")
    wb = None
    names = []

    try:
        wb = excel.Workbooks.Open(file_path)
        sheet_names = [sheet.Name for sheet in wb.Worksheets]
        if "Scores" not in sheet_names:
            raise ValueError("Sheet 'Scores' not found in the workbook.")

        sheet = wb.Worksheets("Scores")
        i = 4
        while True:
            first = sheet.Cells(i, 1).Value
            last = sheet.Cells(i, 2).Value
            if not first and not last:
                break
            if first and last:
                names.append(f"{first} {last}")
            i += 1
    finally:
        if wb:
            wb.Close(SaveChanges=0)
        excel.Quit()

    return names

def get_available_players():
    return cache.get_available_players()

def get_submitted_player_count():
    return cache.get_submitted_player_count()

def reset_excel_cache():
    cache.refresh()
