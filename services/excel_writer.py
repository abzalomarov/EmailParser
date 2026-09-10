import io

from openpyxl import Workbook

HEADERS = ["Name", "Phone", "Subject", "Urgency"]


def build_workbook_bytes(rows: list) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Parsed Emails"
    ws.append(HEADERS)
    for row in rows:
        ws.append([row.get("name", ""), row.get("phone", ""), row.get("subject", ""), row.get("urgency", "")])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
