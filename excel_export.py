"""Formatted Excel workbook builder."""
import io

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F3A5F")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TOTAL_FONT = Font(bold=True)
TOP_BORDER = Border(top=Side(style="thin"), bottom=Side(style="double"))
OK_FILL = PatternFill("solid", fgColor="D9F2E0")
BAD_FILL = PatternFill("solid", fgColor="FADBD8")
MONEY = "#,##0.00"
DATE = "yyyy-mm-dd"

NUMFMT = {c: MONEY for c in ("subtotal", "tax", "total", "unit_price", "amount",
                             "subtotal_sum", "tax_sum", "total_sum", "qty_kgs")}
NUMFMT["qty_ctns"] = "#,##0"
DATE_COLS = {"invoice_date", "production_date", "expiry_date"}


def _pretty(name: str) -> str:
    return name.replace("_", " ").title()


def _style_sheet(ws, df: pd.DataFrame, total_cols=()):
    n = len(df)
    for c in range(1, len(df.columns) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font = HEADER_FILL, HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.value = _pretty(str(cell.value))
    ws.row_dimensions[1].height = 24
    ws.freeze_panes = "A2"
    if n:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{n + 1}"

    for i, col in enumerate(df.columns, start=1):
        letter = get_column_letter(i)
        sample = [len(str(v)) for v in df[col].head(300) if pd.notna(v)]
        ws.column_dimensions[letter].width = min(max([len(_pretty(str(col)))] + sample) + 3, 55)
        for r in range(2, n + 2):
            cell = ws.cell(row=r, column=i)
            if col in NUMFMT:
                cell.number_format = NUMFMT[col]
            elif col in DATE_COLS:
                cell.number_format = DATE
            if col == "status":
                cell.fill = OK_FILL if cell.value == "OK" else BAD_FILL
                cell.alignment = Alignment(horizontal="center")

    if total_cols and n:
        tr = n + 2
        ws.cell(row=tr, column=1, value="TOTAL").font = TOTAL_FONT
        for col in total_cols:
            i = list(df.columns).index(col) + 1
            L = get_column_letter(i)
            cell = ws.cell(row=tr, column=i, value=f"=SUM({L}2:{L}{n + 1})")
            cell.number_format = NUMFMT.get(col, MONEY)
            cell.font = TOTAL_FONT
        for i in range(1, len(df.columns) + 1):
            ws.cell(row=tr, column=i).border = TOP_BORDER


def build_packing_workbook(lines: pd.DataFrame, summary: pd.DataFrame, checks: pd.DataFrame) -> bytes:
    lines = lines.copy()
    for c in ("production_date", "expiry_date"):
        lines[c] = pd.to_datetime(lines[c], errors="coerce")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl", datetime_format=DATE) as w:
        for name, df, totals in [
            ("Packing Lines", lines, ("qty_ctns", "qty_kgs")),
            ("Item Summary", summary, ("qty_ctns", "qty_kgs")),
            ("Checks", checks, ()),
        ]:
            df.to_excel(w, sheet_name=name, index=False)
            _style_sheet(w.sheets[name], df, totals)
    return buf.getvalue()


def build_workbook(inv: pd.DataFrame, items: pd.DataFrame, checks: pd.DataFrame,
                   vendor_summary: pd.DataFrame) -> bytes:
    inv = inv.copy()
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"], errors="coerce")
    labels = inv.set_index("id")[["vendor", "invoice_number"]]
    its = items.dropna(subset=["invoice_id"]).copy()
    its.insert(1, "vendor", its["invoice_id"].map(labels["vendor"]))
    its.insert(2, "invoice_number", its["invoice_id"].map(labels["invoice_number"]))

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl", datetime_format=DATE) as w:
        sheets = [
            ("Invoices", inv, ("subtotal", "tax", "total")),
            ("Line Items", its, ("amount",)),
            ("Vendor Summary", vendor_summary, ("subtotal_sum", "tax_sum", "total_sum")),
            ("Checks", checks, ()),
        ]
        for name, df, totals in sheets:
            df.to_excel(w, sheet_name=name, index=False)
            _style_sheet(w.sheets[name], df, totals)
    return buf.getvalue()
