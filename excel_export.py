#   excel_export.py

import json
import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.worksheet.properties import PageSetupProperties

THIN = Side(style="thin")

# (key in the JSON, header shown in Excel), in the order of your sample sheet
REV_COLUMNS = [
    ("Rev. No. :",    "REV. NO."),
    ("Date :",        "DATE"),
    ("Description :", "DESCRIPTION"),
    ("Prepared By :", "PREPARED BY"),
    ("Checked By :",  "CHECKED BY"),
    ("Approved By :", "APPROVED BY"),
]


def _outline(ws, r1, c1, r2, c2):
    """Thin border around a block of cells (no lines inside)."""
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(r, c).border = Border(
                left=THIN if c == c1 else None,
                right=THIN if c == c2 else None,
                top=THIN if r == r1 else None,
                bottom=THIN if r == r2 else None)


def _build(data, logo_path):
    rev, doc = data["rev"], data["doc"]

    wb = Workbook()
    ws = wb.active
    ws.title = "CoverPage"
    ws.sheet_view.showGridLines = False
    for col, width in zip("ABCDEFGH", [3, 14, 14, 24, 20, 20, 20, 3]):
        ws.column_dimensions[col].width = width

    # ---- logo (optional) ------------------------------------------------
    if logo_path and os.path.exists(logo_path):
        try:
            from openpyxl.drawing.image import Image
            img = Image(logo_path)
            ratio = 60 / img.height
            img.width, img.height = int(img.width * ratio), 60
            ws.add_image(img, "B2")
        except Exception:
            pass                       # Pillow missing or bad image: skip the logo

    # ---- cover-page table (rows 6 onwards, like your sample) ------------
    row = 6
    for label, value in doc.items():
        if label == "Rev. No. :":      # shown inside the first row instead
            continue
        name = label.split(":")[0].strip().rstrip(".")   # 'VENDOR :    M/s.' -> 'VENDOR'
        if name == "VENDOR" and not value.upper().startswith("M/S"):
            value = "M/s. " + value
        first = (row == 6)

        ws.row_dimensions[row].height = 22
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        ws.merge_cells(start_row=row, start_column=5, end_row=row,
                       end_column=6 if first else 7)

        c = ws.cell(row, 2, f"{name}  :")
        c.font = Font(bold=True, size=11)
        c.alignment = Alignment(horizontal="right", vertical="center")

        v = ws.cell(row, 5, value)
        v.font = Font(size=10)
        v.alignment = Alignment(horizontal="left", vertical="center",
                                indent=1, shrink_to_fit=True)

        _outline(ws, row, 2, row, 7)
        if first:                      # REV. box at the right of the first row
            r = ws.cell(row, 7, f"REV.   :   {doc.get('Rev. No. :', '')}")
            r.font = Font(bold=True, size=11)
            r.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            r.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
        row += 1

    # ---- revision table at the bottom: newest on top, header below ------
    n = len(rev.get("Rev. No. :", []))
    header_row = max(34, 18 + n)
    for col, (_, title) in enumerate(REV_COLUMNS, start=2):
        h = ws.cell(header_row, col, title)
        h.font = Font(bold=True, size=10)
        h.alignment = Alignment(horizontal="center", vertical="center")
        h.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

    for k, i in enumerate(reversed(range(n))):       # newest revision first
        r = header_row - n + k
        for col, (key, _) in enumerate(REV_COLUMNS, start=2):
            cell = ws.cell(r, col, rev[key][i])
            cell.font = Font(size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

    # ---- print setup: one landscape page ---------------------------------
    ws.print_area = f"A1:H{header_row + 2}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    return wb


def generate_excel(json_path, xlsx_path, logo_path=None):
    """Creates the Excel file, then deletes the JSON (only if the save worked)."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    wb = _build(data, logo_path)
    wb.save(xlsx_path)        # raises PermissionError if that file is open in Excel/WPS
    os.remove(json_path)      # reached only after a successful save


