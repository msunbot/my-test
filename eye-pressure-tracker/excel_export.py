import io

from openpyxl import Workbook
from openpyxl.styles import Font


def build_workbook(readings) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Eye Pressure"

    headers = ["Date", "Time", "Pressure Left", "Pressure Right"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in readings:
        ws.append([row["date"], row["time"], row["pressure_left"], row["pressure_right"]])

    for col_letter, width in zip("ABCD", [12, 10, 14, 15]):
        ws.column_dimensions[col_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
