import os
import win32com.client
import pythoncom

EXCEL_PATH = None
_excel_app = None
_workbook = None

class ExcelCache:
    @staticmethod
    def get_excel_path():
        global EXCEL_PATH
        if EXCEL_PATH:
            return EXCEL_PATH

        root_dir = os.path.dirname(os.path.dirname(__file__))
        for file in os.listdir(root_dir):
            if file.endswith("Callaway scoring sheet.xls"):
                EXCEL_PATH = os.path.join(root_dir, file)
                break

        if not EXCEL_PATH:
            raise FileNotFoundError("No Callaway scoring sheet file found")

        return EXCEL_PATH

    @staticmethod
    def get_workbook():
        global _workbook, _excel_app
        if _workbook:
            return _workbook

        pythoncom.CoInitialize()  # ✅ Required to avoid COM error

        path = ExcelCache.get_excel_path()
        _excel_app = win32com.client.Dispatch("Excel.Application")
        _excel_app.Visible = False
        _workbook = _excel_app.Workbooks.Open(path)
        return _workbook

    @staticmethod
    def get_sheet():
        return ExcelCache.get_workbook().Sheets(2)  # 👈 Always "Scores"

    @staticmethod
    def get_total_players(sheet=None):
        if sheet is None:
            wb = ExcelCache.get_workbook()
            try:
                sheet = wb.Sheets(2)  # ✅ Force second sheet, which is 'Scores'
                print(f"✅ Loaded worksheet: {sheet.Name}")
            except Exception as e:
                print(f"❌ Could not load sheet 2 (Scores): {e}")
                return 0

        print("🧪 Scanning for valid players in Scores! (A10:B159)")
        name_data = sheet.Range("A10:B159").Value
        count = 0

        for i, row in enumerate(name_data, start=10):
            first, last = row
            print(f"🔍 Row {i}: First='{first}', Last='{last}'")

            if isinstance(first, str) and isinstance(last, str):
                count += 1
                print(f"✅ Counted as player #{count}")
            else:
                print(f"⏭️ Skipped row {i}")

        print(f"🎯 Total valid players found: {count}")
        return count

    @staticmethod
    def get_submitted_player_count():
        wb = ExcelCache.get_workbook()
        sheet = wb.Sheets(2)  # ✅ Force to "Scores"

        name_data = sheet.Range("A10:B159").Value
        score_data = sheet.Range("D10:U159").Value
        count = 0

        for name_row, score_row in zip(name_data, score_data):
            first, last = name_row
            if isinstance(first, str) and isinstance(last, str) and any(score_row):
                count += 1

        return count

    @staticmethod
    def get_submitted_players(sheet):
        submitted_names = []
        name_data = sheet.Range("A10:B159").Value
        score_data = sheet.Range("D10:U159").Value

        for name_row, score_row in zip(name_data, score_data):
            first, last = name_row
            if isinstance(first, str) and isinstance(last, str) and any(score_row):
                submitted_names.append(f"{first} {last}")

        return submitted_names

    @staticmethod
    def refresh_cache():
        global _workbook, _excel_app
        if _workbook:
            try:
                _workbook.Close(SaveChanges=True)
            except Exception as e:
                print(f"⚠️ Couldn't close workbook (might be dead): {e}")
        _workbook = None
        _excel_app = None
