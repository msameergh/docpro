"""Consistency checks on extracted invoices. Pure pandas, no I/O."""
import pandas as pd

CHECK_COLUMNS = ["invoice_id", "invoice", "severity", "issue"]


def _label(row) -> str:
    vendor = row.get("vendor") or "Unknown vendor"
    number = row.get("invoice_number") or "no number"
    return f"{vendor} / {number}"


def validate(inv: pd.DataFrame, items: pd.DataFrame, tol: float = 0.02) -> pd.DataFrame:
    """Return one row per problem found. Empty frame means everything checks out."""
    rows = []

    def add(row, severity, issue):
        rows.append({"invoice_id": row["id"], "invoice": _label(row), "severity": severity, "issue": issue})

    items = items.dropna(subset=["invoice_id"]) if len(items) else items

    for _, r in inv.iterrows():
        for col, name in [("vendor", "vendor"), ("invoice_number", "invoice number"),
                          ("invoice_date", "invoice date"), ("total", "total")]:
            if pd.isna(r[col]) or r[col] == "":
                add(r, "Error", f"Missing {name}")

        its = items[items["invoice_id"] == r["id"]] if len(items) else items
        if len(its) == 0:
            add(r, "Warning", "No line items extracted")
        else:
            for _, li in its.iterrows():
                q, p, a = li.get("quantity"), li.get("unit_price"), li.get("amount")
                if pd.notna(q) and pd.notna(p) and pd.notna(a) and abs(q * p - a) > tol * max(1, abs(a)) / 2 + tol:
                    add(r, "Warning", f"Line '{li.get('description')}': {q:g} x {p:,.2f} = {q * p:,.2f}, but amount is {a:,.2f}")

            line_sum = its["amount"].sum(min_count=1)
            if pd.notna(line_sum):
                if pd.notna(r["subtotal"]):
                    if abs(line_sum - r["subtotal"]) > tol:
                        add(r, "Error", f"Line items sum to {line_sum:,.2f} but subtotal is {r['subtotal']:,.2f}")
                elif pd.notna(r["total"]) and abs(line_sum + (r["tax"] if pd.notna(r["tax"]) else 0) - r["total"]) > tol:
                    add(r, "Error", f"Line items (+tax) give {line_sum + (r['tax'] if pd.notna(r['tax']) else 0):,.2f} but total is {r['total']:,.2f}")

        if pd.notna(r["subtotal"]) and pd.notna(r["total"]):
            expected = r["subtotal"] + (r["tax"] if pd.notna(r["tax"]) else 0)
            if abs(expected - r["total"]) > tol:
                add(r, "Error", f"Subtotal + tax = {expected:,.2f} but total is {r['total']:,.2f}")

    # duplicates
    keyed = inv.dropna(subset=["vendor", "invoice_number"])
    dups = keyed[keyed.duplicated(["vendor", "invoice_number"], keep=False)]
    for _, r in dups.iterrows():
        add(r, "Warning", "Possible duplicate (same vendor and invoice number)")

    return pd.DataFrame(rows, columns=CHECK_COLUMNS)


def status_by_invoice(inv: pd.DataFrame, checks: pd.DataFrame) -> pd.Series:
    bad = set(checks["invoice_id"]) if len(checks) else set()
    return inv["id"].map(lambda i: "Review" if i in bad else "OK")
