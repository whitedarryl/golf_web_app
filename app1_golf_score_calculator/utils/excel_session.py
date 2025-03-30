# utils/excel_session.py
import win32com.client

_excel_app = None
_workbook = None

def get_excel_workbook(file_path):
    global _excel_app, _workbook
    if _excel_app is None:
        print("🔗 Launching Excel session...")
        _excel_app = win32com.client.Dispatch("Excel.Application")
        _excel_app.Visible = False
        _workbook = _excel_app.Workbooks.Open(file_path)
    return _workbook

def close_excel():
    global _excel_app, _workbook
    if _workbook:
        _workbook.Save()
        _workbook.Close(False)
    if _excel_app:
        _excel_app.Quit()
    _excel_app = None
    _workbook = None
