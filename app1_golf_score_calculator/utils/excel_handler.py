import os
from .excel_session import get_excel_workbook
from datetime import datetime

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Delcastle August 2023 Callaway scoring sheet.xls")

def update_excel(name, scores, out, inn, total):
    wb = get_excel_workbook(EXCEL_PATH)
    ws = wb.Sheets(1)

    # 👇 your existing Excel writing logic goes here
    for row in range(4, 120):  # assuming players are listed in row 4 and below
        first = str(ws.Cells(row, 2).Value).strip()
        last = str(ws.Cells(row, 3).Value).strip()
        full = f"{first} {last}".strip()

        if full.lower() == name.strip().lower():
            print(f"✅ Writing score for: {name}")
            for i, score in enumerate(scores):
                ws.Cells(row, 6 + i).Value = score
            ws.Cells(row, 25).Value = out
            ws.Cells(row, 26).Value = inn
            ws.Cells(row, 27).Value = total
            ws.Cells(row, 28).Value = datetime.now().strftime("%m/%d/%Y %H:%M")
            break


# def update_excel(file_path, player_name, scores):
#     pythoncom.CoInitialize()
#     excel = None
#     workbook = None
#     sheet = None

#     try:
#         excel = win32.gencache.EnsureDispatch('Excel.Application')
#         excel.Visible = False
#         workbook = excel.Workbooks.Open(file_path)
#         sheet = workbook.Sheets(1)

#         print(f"🔄 Refreshing Excel cache...")
#         row = find_player_row(sheet, player_name)
#         if row:
#             for i, score in enumerate(scores, start=2):
#                 sheet.Cells(row, i).Value = score
#             print(f"✅ Score written to archive for: {player_name}")
#         else:
#             print(f"⚠️ Player {player_name} not found.")

#         workbook.Save()

#     except Exception as ex:
#         print(f"❌ Excel error: {ex}")

#     finally:
#         try:
#             if workbook:
#                 workbook.Close(SaveChanges=True)
#         except:
#             pass  # Silently skip if workbook dies
#         try:
#             if excel:
#                 excel.Quit()
#         except Exception as e:
#             print(f"⚠️ Couldn't quit Excel properly: {e}")

#         for obj in [sheet, workbook, excel]:
#             try:
#                 del obj
#             except:
#                 pass

#         pythoncom.CoUninitialize()


def find_player_row(sheet, player_name):
    for row in range(2, 500):
        cell_value = sheet.Cells(row, 1).Value
        if str(cell_value).strip().lower() == player_name.strip().lower():
            return row
    return None
