"""Packing-list helpers: item master lookup and consistency checks. Pure pandas."""
import difflib
import re
from pathlib import Path

import pandas as pd

MASTER_PATH = Path(__file__).parent / "data" / "item_master.csv"
FUZZY_CUTOFF = 0.88

COLUMNS = ["source_file", "packing_list_no", "item_code", "item_description", "document_description",
           "production_date", "expiry_date", "qty_ctns", "qty_kgs", "match", "match_note"]
# Columns that are internal to the review screen and not exported
REVIEW_ONLY = ["document_description", "match", "match_note"]
CHECK_COLUMNS = ["row", "item", "severity", "issue"]


def _norm(s) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(s).upper()).strip()


# ---------- item master ----------
def read_master_raw(file) -> pd.DataFrame:
    """Read an uploaded CSV/XLSX as text, untouched apart from trimmed headers."""
    name = getattr(file, "name", str(file)).lower()
    df = pd.read_csv(file, dtype=str) if name.endswith(".csv") else pd.read_excel(file, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def guess_columns(df: pd.DataFrame) -> tuple[str, str]:
    """Best guess of (code column, description column) from the headers."""
    cols = list(df.columns)
    code = next((c for c in cols if "code" in c.lower() or c.lower() in ("sku", "item", "item no", "item #")), cols[0])
    rest = [c for c in cols if c != code]
    desc = next((c for c in rest if "desc" in c.lower() or "name" in c.lower() or "product" in c.lower()),
                rest[0] if rest else code)
    return code, desc


def build_master(df: pd.DataFrame, code_col: str, desc_col: str) -> tuple[pd.DataFrame, dict]:
    """Clean the chosen columns into the item master. Returns (master, stats)."""
    out = df[[code_col, desc_col]].rename(columns={code_col: "item_code", desc_col: "item_description"})
    total = len(out)
    out = out.dropna().astype(str).apply(lambda s: s.str.strip())
    out = out[(out["item_code"] != "") & (out["item_description"] != "")]
    blank = total - len(out)
    dup_desc = int(out.duplicated("item_description").sum())
    out = out.drop_duplicates("item_description")
    conflicts = int(out.assign(k=out["item_description"].map(_norm)).duplicated("k").sum())
    return out, {"rows": total, "blank_dropped": blank, "duplicate_descriptions": dup_desc,
                 "near_duplicates": conflicts}


def template_bytes() -> bytes:
    import io
    sample = pd.DataFrame({
        "Item Code": ["CHK-HB-16", "CHK-DS-108", "CHK-LV-9"],
        "Item Description": [
            "FROZEN CHICKEN - HALF BREAST BONELESS SKINLESS WITHOUT INNER FILLET AL ISLAMI BRAND 1KG X 16 = 16KG",
            "FROZEN CHICKEN - DRUMSTICK AL ISLAMI BRAND 900G X 12 = 10.80 KG",
            "FROZEN CHICKEN - LIVER AL ISLAMI BRAND 450G X 20 = 9 KG",
        ],
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        sample.to_excel(w, index=False, sheet_name="Item Master")
        ws = w.sheets["Item Master"]
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 100
    return buf.getvalue()


def clear_master():
    MASTER_PATH.unlink(missing_ok=True)


def save_master(df: pd.DataFrame):
    MASTER_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(MASTER_PATH, index=False)


def get_master() -> pd.DataFrame:
    if MASTER_PATH.exists():
        return pd.read_csv(MASTER_PATH, dtype=str)
    return pd.DataFrame(columns=["item_code", "item_description"])


def lookup_codes(descriptions: pd.Series, master: pd.DataFrame, existing: pd.Series = None):
    """Return (codes, match_kind). Codes already printed on the document are kept."""
    keys = {_norm(d): c for d, c in zip(master["item_description"], master["item_code"])}
    codes, kinds = [], []
    for i, d in enumerate(descriptions):
        have = existing.iloc[i] if existing is not None else None
        if isinstance(have, str) and have.strip():
            codes.append(have.strip()); kinds.append("Document")
            continue
        n = _norm(d) if pd.notna(d) else ""
        if n in keys:
            codes.append(keys[n]); kinds.append("Exact")
            continue
        close = difflib.get_close_matches(n, list(keys), n=1, cutoff=FUZZY_CUTOFF) if n and keys else []
        if close:
            codes.append(keys[close[0]]); kinds.append("Approximate")
        else:
            codes.append(None); kinds.append("Not found")
    return codes, kinds


RAW_COLUMNS = ["source_file", "packing_list_no", "doc_item_code", "document_description",
               "production_date", "expiry_date", "qty_ctns", "qty_kgs"]


def assemble_lines(raw: pd.DataFrame, master: pd.DataFrame, found: dict) -> pd.DataFrame:
    """Raw extracted rows + match results -> review table using the master's descriptions.

    `found` maps a document description to (item_code, confidence, reason).
    Rows with the same item and production date are combined.
    """
    if raw.empty:
        return pd.DataFrame(columns=COLUMNS)
    df = raw.copy()
    names = dict(zip(master["item_code"], master["item_description"]))

    def resolve(r):
        if r["doc_item_code"]:
            return pd.Series([r["doc_item_code"], "Document", ""])
        code, conf, why = found.get(r["document_description"], (None, "Not found", ""))
        return pd.Series([code, conf, why])

    df[["item_code", "match", "match_note"]] = df.apply(resolve, axis=1)
    df["item_description"] = [names.get(c) or d for c, d in zip(df["item_code"], df["document_description"])]
    keys = ["source_file", "packing_list_no", "item_code", "item_description", "production_date", "expiry_date"]
    join = lambda s: " | ".join(dict.fromkeys(s.dropna().astype(str)))
    df = df.groupby(keys, dropna=False, as_index=False, sort=False).agg(
        document_description=("document_description", join), match=("match", "first"),
        match_note=("match_note", "first"), qty_ctns=("qty_ctns", "sum"), qty_kgs=("qty_kgs", "sum"))
    df["production_date"] = pd.to_datetime(df["production_date"], errors="coerce")
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")
    return df[COLUMNS]


# ---------- checks ----------
_CASE_KG = re.compile(r"=\s*(\d+(?:[.,]\d+)?)\s*KGS?\b", re.I)


def case_weight(description) -> float | None:
    """Parse the per-carton weight from text like '1KG X 16 = 16KG'."""
    if not isinstance(description, str):
        return None
    m = _CASE_KG.search(description.replace("\n", " "))
    return float(m.group(1).replace(",", ".")) if m else None


def validate_packing(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, r in df.reset_index(drop=True).iterrows():
        label = str(r["item_description"] or "")[:60] or "(no description)"

        def add(sev, issue):
            rows.append({"row": i + 1, "item": label, "severity": sev, "issue": issue})

        if pd.isna(r["item_description"]) or not str(r["item_description"]).strip():
            add("Error", "Missing item description")
        if pd.isna(r["item_code"]) or not str(r["item_code"]).strip():
            add("Error", "Item code not found. Enter it here or add the product to the item master")
        elif r.get("match") in ("Medium", "Low"):
            note = f" ({r['match_note']})" if isinstance(r.get("match_note"), str) and r["match_note"] else ""
            add("Warning", f"Item code matched with {r['match'].lower()} confidence{note}. Please confirm")
        if pd.isna(r["qty_ctns"]) or r["qty_ctns"] <= 0:
            add("Error", "Missing or zero Qty CTNs")
        if pd.isna(r["qty_kgs"]) or r["qty_kgs"] <= 0:
            add("Error", "Missing or zero Qty Kgs")
        # the pack weight (e.g. '= 16KG') is in the supplier's wording, not the master's
        cw = case_weight(r.get("document_description")) or case_weight(r["item_description"])
        if cw and pd.notna(r["qty_ctns"]) and pd.notna(r["qty_kgs"]):
            expected = r["qty_ctns"] * cw
            if abs(expected - r["qty_kgs"]) > max(0.05, 0.001 * expected):
                add("Warning", f"{r['qty_ctns']:g} CTNs x {cw:g} kg = {expected:,.2f} kg, but Qty Kgs is {r['qty_kgs']:,.2f}")
    return pd.DataFrame(rows, columns=CHECK_COLUMNS)


def status_by_row(df: pd.DataFrame, checks: pd.DataFrame) -> pd.Series:
    bad = set(checks["row"]) if len(checks) else set()
    return pd.Series(["Review" if (i + 1) in bad else "OK" for i in range(len(df))], index=df.index)
