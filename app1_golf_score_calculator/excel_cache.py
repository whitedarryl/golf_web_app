import os
import glob
import pythoncom
import win32com.client


class ExcelCache:
    def __init__(self):
        self.excel = None
        self.wb = None
        self.sheet = None
        self.last_file = None
        self.GOLF_FOLDER = os.getenv("GOLF_WEBAPP_FOLDER", "C:\\Golf Web App_backup")

    def _open_excel(self):
        pythoncom.CoInitialize()
        self.excel = win32com.client.Dispatch("Excel.Application")
        self.excel.Visible = False
        self.excel.DisplayAlerts = False

    def _get_file_path(self):
        pattern = os.path.join(self.GOLF_FOLDER, "*Callaway scoring sheet.xls")
        matches = glob.glob(pattern)
        return matches[0] if matches else None

    def _load(self):
        if self.excel is None:
            self._open_excel()

        file_path = self._get_file_path()
        if not file_path:
            raise FileNotFoundError("Callaway Excel file not found.")

        if self.wb:
            self.wb.Close(SaveChanges=0)

        self.wb = self.excel.Workbooks.Open(file_path)
        self.sheet = self.wb.Worksheets("Scores")
        self.last_file = file_path

    def get_available_players(self):
        sheet = self.get_sheet()
        name_data = sheet.Range("A4:B153").Value
        score_data = sheet.Range("D4:U153").Value

        available = []

        for i in range(len(name_data)):
            first, last = name_data[i]
            if not first and not last:
                break
            full_name = ' '.join(f"{first} {last}".split()).strip()
            row_scores = score_data[i]
            has_score = any(cell not in (None, "", 0) for cell in row_scores)

            if full_name and not has_score:
                available.append(full_name)

        return available

    def get_submitted_player_count(self):
        sheet = self.get_sheet()
        name_data = sheet.Range("A4:B153").Value
        score_data = sheet.Range("D4:U153").Value

        submitted = 0

        for i in range(len(name_data)):
            first, last = name_data[i]
            if not first and not last:
                break
            row_scores = score_data[i]
            has_score = any(cell not in (None, "", 0) for cell in row_scores)

            if first and last and has_score:
                submitted += 1

        return submitted

    def get_total_players(self):
        sheet = self.get_sheet()
        name_data = sheet.Range("A4:B153").Value
        count = 0
        for first, last in name_data:
            if not first and not last:
                break
            if first and last:
                count += 1
        return count

    def refresh(self):
        print("🔄 Refreshing Excel cache...")
        try:
            if self.wb:
                try:
                    self.wb.Close(SaveChanges=0)
                except Exception as e:
                    print("⚠️ Couldn't close workbook (might be dead):", e)
            if self.excel:
                try:
                    self.excel.Quit()
                except Exception as e:
                    print("⚠️ Couldn't quit Excel (might be dead):", e)
        except Exception as e:
            print("⚠️ Unexpected error during refresh cleanup:", e)

        self.wb = None
        self.excel = None
        self.sheet = None
        self.loaded = False
        self._load()

    def get_sheet(self):
        try:
            # Quick poke to test COM connection
            _ = self.sheet.Cells(1, 1).Value
            return self.sheet
        except Exception:
            print("⚠️ Sheet disconnected — reloading Excel.")
            self.refresh()
            return self.sheet

    def close(self):
        if self.wb:
            self.wb.Close(SaveChanges=0)
        if self.excel:
            self.excel.Quit()
        self.wb = self.sheet = self.excel = None
