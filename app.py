import hmac
import os
from datetime import datetime

import pandas as pd
import streamlit as st

import landing as landing_page
import matcher
import packing
from excel_export import build_packing_workbook, build_workbook
from extractor import (DEFAULT_PROMPT, PACKING_PROMPT, extract_invoices,
                       extract_packing_lists)
from validation import status_by_invoice, validate

st.set_page_config(page_title="Docpro | Document Extraction", page_icon=":material/receipt_long:", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #F5F7FA; border: 1px solid #E3E8EF; padding: 14px 18px; border-radius: 10px;}
h1 {margin-bottom: 0;}
</style>
""", unsafe_allow_html=True)


MIME = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def secret(name: str):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name)


def require_login():
    """Optional shared-password gate: active only when APP_PASSWORD is configured."""
    pw = secret("APP_PASSWORD")
    if st.session_state.get("authed"):
        landing_page.inject_css()
        return
    if landing_page.landing(bool(pw), lambda e: hmac.compare_digest(e, str(pw))):
        st.session_state["authed"] = True
        st.rerun()
    st.stop()


def to_date(s):
    return pd.to_datetime(s, errors="coerce")


# =====================================================================
# Packing lists
# =====================================================================
def item_master_panel(master: pd.DataFrame):
    """Sidebar panel to upload, review and replace the item master."""
    with st.expander(f"Item master ({len(master)} items)" if len(master) else "Item master (not loaded)",
                     expanded=master.empty):
        st.markdown(
            "**Required columns**\n"
            "- **Item Code**: your internal code for the product\n"
            "- **Item Description**: the product name *as it appears on the packing list*, "
            "including brand and pack size (e.g. `... AL ISLAMI BRAND 900G X 12 = 10.80 KG`)\n\n"
            "One row per product. Other columns are ignored. Excel (.xlsx) or CSV."
        )
        st.download_button("Download template", packing.template_bytes(), "item_master_template.xlsx",
                           mime=XLSX, use_container_width=True)

        up = st.file_uploader("Upload item master", type=["xlsx", "xls", "csv"], key="pk_master")
        if up is not None:
            try:
                raw = packing.read_master_raw(up)
            except Exception as e:
                st.error(f"Could not read the file: {e}")
                raw = None
            if raw is not None and raw.shape[1] < 2:
                st.error("The file needs at least two columns: item code and item description.")
            elif raw is not None:
                gc, gd = packing.guess_columns(raw)
                cols = list(raw.columns)
                code_col = st.selectbox("Item code column", cols, index=cols.index(gc))
                desc_col = st.selectbox("Item description column", cols, index=cols.index(gd))
                if code_col == desc_col:
                    st.error("Choose two different columns.")
                else:
                    new, stats = packing.build_master(raw, code_col, desc_col)
                    st.caption(f"Preview: {len(new)} valid products")
                    st.dataframe(new.head(5), hide_index=True, use_container_width=True)
                    if stats["blank_dropped"]:
                        st.warning(f"{stats['blank_dropped']} rows skipped (missing code or description).")
                    if stats["duplicate_descriptions"]:
                        st.warning(f"{stats['duplicate_descriptions']} duplicate descriptions removed "
                                   "(first code kept).")
                    if stats["near_duplicates"]:
                        st.warning(f"{stats['near_duplicates']} descriptions differ only by spacing or "
                                   "punctuation. Check for conflicting codes.")
                    if new.empty:
                        st.error("No valid rows found.")
                    elif st.button("Save item master", type="primary", use_container_width=True):
                        packing.save_master(new)
                        st.rerun()

        if len(master):
            st.divider()
            st.caption("Currently saved (replaced when you save a new file):")
            st.dataframe(master.head(5), hide_index=True, use_container_width=True)
            if st.button("Remove saved item master", use_container_width=True):
                packing.clear_master()
                st.rerun()



def packing_page(api_key: str):
    with st.sidebar:
        st.header("1. Upload")
        files = st.file_uploader("Packing lists (PDF or image)", type=list(MIME),
                                 accept_multiple_files=True, key="pk_files")

        master = packing.get_master()
        item_master_panel(master)
        with st.expander("Advanced"):
            prompt = st.text_area("Extraction instructions", PACKING_PROMPT, height=260)

        run = st.button("Extract packing lists", type="primary", use_container_width=True, disabled=not files)
        if st.session_state.get("pk") is not None and st.button("Clear results", use_container_width=True):
            for k in ("pk", "pk_errors"):
                st.session_state.pop(k, None)
            st.rerun()

    st.title("Packing List Extraction")
    st.caption("Extract item code, description, cartons and kilograms. Review, then export to Excel.")

    if run:
        frames, errors = [], []
        bar = st.progress(0.0, text="Starting...")
        for n, f in enumerate(files, start=1):
            bar.progress((n - 1) / len(files), text=f"Reading {f.name} ({n}/{len(files)})")
            try:
                for pl in extract_packing_lists(api_key, f.getvalue(), MIME[f.name.rsplit(".", 1)[-1].lower()], prompt):
                    for ln in pl.lines:
                        frames.append({
                            "source_file": f.name, "packing_list_no": pl.document_number,
                            "doc_item_code": (ln.item_code or "").strip() or None,
                            "document_description": " ".join(ln.description.split()) if ln.description else None,
                            "production_date": ln.production_date, "expiry_date": ln.expiry_date,
                            "qty_ctns": ln.cartons, "qty_kgs": ln.net_weight_kg,
                        })
            except Exception as e:
                errors.append(f"{f.name}: {e}")

        raw = pd.DataFrame(frames, columns=packing.RAW_COLUMNS)
        found = {}
        if not raw.empty:
            bar.progress(0.9, text="Matching items to your item master...")
            todo = raw.loc[raw["doc_item_code"].isna(), "document_description"].dropna().tolist()
            try:
                found = matcher.match_descriptions(api_key, todo, master) if todo else {}
            except Exception as e:
                errors.append(f"AI item matching failed ({e}); used text similarity instead")
                found = matcher.fallback_match(todo, master) if (todo and not master.empty) else {}
        bar.empty()
        st.session_state["pk"] = packing.assemble_lines(raw, master, found)
        st.session_state["pk_errors"] = errors
        st.session_state["pk_gen"] = st.session_state.get("pk_gen", 0) + 1

    for e in st.session_state.get("pk_errors", []):
        st.error(f"Could not process {e}")

    if st.session_state.get("pk") is None:
        if master.empty:
            st.warning("No item master loaded yet. Item codes will be blank until you upload one "
                       "(sidebar > Item master).")
        st.info("Upload one or more packing lists in the sidebar, then click **Extract packing lists**.")
        st.stop()
    if st.session_state["pk"].empty:
        st.warning("No lines were extracted.")
        st.stop()

    gen = st.session_state["pk_gen"]
    tab_review, tab_summary = st.tabs(["Review lines", "Item summary"])

    with tab_review:
        st.caption("Items are matched to your item master by AI. Where Match is Medium/Low or the code is "
                   "missing, pick the right code from the Item code dropdown. The description then follows "
                   "your master. Edit quantities if needed.")
        stored = st.session_state["pk"]
        known = list(dict.fromkeys(list(master["item_code"]) + [c for c in stored["item_code"].dropna()]))
        code_col = (st.column_config.SelectboxColumn("Item code", options=known, width="small")
                    if 0 < len(known) <= 3000 else st.column_config.TextColumn("Item code", width="small"))
        edited = st.data_editor(
            stored, key=f"pk_{gen}", hide_index=True, use_container_width=True,
            num_rows="dynamic", disabled=["source_file", "item_description", "document_description", "match", "match_note"],
            column_order=["source_file", "packing_list_no", "item_code", "item_description", "production_date",
                          "expiry_date", "qty_ctns", "qty_kgs", "match", "document_description", "match_note"],
            column_config={
                "source_file": "File",
                "packing_list_no": "Packing list #",
                "item_code": code_col,
                "item_description": st.column_config.TextColumn("Item description (master)", width="large"),
                "document_description": st.column_config.TextColumn("Description on document", width="large"),
                "production_date": st.column_config.DateColumn("Production date", format="YYYY-MM-DD"),
                "expiry_date": st.column_config.DateColumn("Expiry date", format="YYYY-MM-DD"),
                "qty_ctns": st.column_config.NumberColumn("Qty CTNs", format="%d"),
                "qty_kgs": st.column_config.NumberColumn("Qty Kgs", format="%.2f"),
                "match": st.column_config.TextColumn("Match", width="small"),
                "match_note": "Why",
            },
        )
        # Description always follows the master for the chosen code.
        names = dict(zip(master["item_code"], master["item_description"]))
        lines = edited.copy()
        lines["item_description"] = [names.get(c) or d for c, d in zip(lines["item_code"], lines["item_description"])]

    checks = packing.validate_packing(lines)
    status = packing.status_by_row(lines, checks)

    summary = (
        lines.assign(item_code=lines["item_code"].fillna("(none)"))
        .groupby(["item_code", "item_description"], as_index=False, dropna=False)
        .agg(qty_ctns=("qty_ctns", "sum"), qty_kgs=("qty_kgs", "sum"))
        .sort_values("item_code")
    )

    with tab_summary:
        st.dataframe(summary, hide_index=True, use_container_width=True, column_config={
            "item_code": "Item code", "item_description": "Item description",
            "qty_ctns": st.column_config.NumberColumn("Qty CTNs", format="%d"),
            "qty_kgs": st.column_config.NumberColumn("Qty Kgs", format="%.2f")})

    with tab_review:
        st.subheader("Checks")
        if checks.empty:
            st.success("All checks passed.")
        else:
            st.dataframe(checks, hide_index=True, use_container_width=True,
                         column_config={"row": st.column_config.NumberColumn("Row", width="small"),
                                        "item": "Item", "severity": "Severity", "issue": "Issue"})

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Lines", len(lines))
    m2.metric("Total CTNs", f"{lines['qty_ctns'].sum():,.0f}")
    m3.metric("Total Kgs", f"{lines['qty_kgs'].sum():,.2f}")
    m4.metric("Rows need review", int((status == "Review").sum()))

    export = lines.drop(columns=packing.REVIEW_ONLY).assign(status=status)
    st.download_button("Download Excel report", data=build_packing_workbook(export, summary, checks),
                       file_name=f"packing_lists_{datetime.now():%Y%m%d_%H%M}.xlsx", mime=XLSX, type="primary")


# =====================================================================
# Invoices
# =====================================================================
def invoice_page(api_key: str):
    with st.sidebar:
        st.header("1. Upload")
        files = st.file_uploader("Invoices (PDF or image)", type=list(MIME), accept_multiple_files=True, key="inv_files")
        with st.expander("Advanced"):
            prompt = st.text_area("Extraction instructions", DEFAULT_PROMPT, height=260)
            tol = st.number_input("Rounding tolerance", 0.0, 5.0, 0.02, 0.01,
                                  help="Differences up to this amount are not flagged.")
        run = st.button("Extract invoices", type="primary", use_container_width=True, disabled=not files)
        if st.session_state.get("inv") is not None and st.button("Clear results", use_container_width=True):
            for k in ("inv", "items", "errors"):
                st.session_state.pop(k, None)
            st.rerun()

    st.title("Invoice Extraction")
    st.caption("Upload invoices, review flagged items, and export a formatted Excel report.")

    if run:
        inv_rows, item_rows, errors = [], [], []
        bar = st.progress(0.0, text="Starting...")
        next_id = 1
        for n, f in enumerate(files, start=1):
            bar.progress((n - 1) / len(files), text=f"Reading {f.name} ({n}/{len(files)})")
            try:
                for inv in extract_invoices(api_key, f.getvalue(), MIME[f.name.rsplit(".", 1)[-1].lower()], prompt):
                    d = inv.model_dump(exclude={"line_items"})
                    inv_rows.append({"id": next_id, "source_file": f.name, **d})
                    for li in inv.line_items:
                        item_rows.append({"invoice_id": next_id, **li.model_dump()})
                    next_id += 1
            except Exception as e:
                errors.append(f"{f.name}: {e}")
        bar.empty()

        inv_df = pd.DataFrame(inv_rows, columns=["id", "source_file", "vendor", "invoice_number", "invoice_date",
                                                 "currency", "subtotal", "tax", "total"])
        inv_df["invoice_date"] = to_date(inv_df["invoice_date"])
        st.session_state["inv"] = inv_df
        st.session_state["items"] = pd.DataFrame(item_rows, columns=["invoice_id", "description", "quantity",
                                                                     "unit_price", "amount"])
        st.session_state["errors"] = errors
        st.session_state["editor_gen"] = st.session_state.get("editor_gen", 0) + 1

    for e in st.session_state.get("errors", []):
        st.error(f"Could not process {e}")

    if st.session_state.get("inv") is None:
        st.info("Upload one or more invoices in the sidebar, then click **Extract invoices**.")
        st.stop()
    if st.session_state["inv"].empty:
        st.warning("No invoices were extracted.")
        st.stop()

    gen = st.session_state["editor_gen"]
    money = st.column_config.NumberColumn(format="%.2f")
    tab_review, tab_items, tab_summary = st.tabs(["Review invoices", "Line items", "Vendor summary"])

    with tab_review:
        st.caption("Edit any cell to correct it. Checks below update automatically.")
        inv = st.data_editor(
            st.session_state["inv"], key=f"inv_{gen}", hide_index=True, use_container_width=True,
            disabled=["id", "source_file"],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "source_file": "File", "vendor": "Vendor", "invoice_number": "Invoice #",
                "invoice_date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "currency": st.column_config.TextColumn("Cur.", width="small"),
                "subtotal": st.column_config.NumberColumn("Subtotal", format="%.2f"),
                "tax": st.column_config.NumberColumn("Tax", format="%.2f"),
                "total": st.column_config.NumberColumn("Total", format="%.2f"),
            },
        )

    with tab_items:
        st.caption("Line items by invoice ID. Add or delete rows as needed.")
        items = st.data_editor(
            st.session_state["items"], key=f"items_{gen}", hide_index=True, use_container_width=True,
            num_rows="dynamic",
            column_config={
                "invoice_id": st.column_config.NumberColumn("Invoice ID", width="small", step=1),
                "description": "Description",
                "quantity": st.column_config.NumberColumn("Qty", format="%g"),
                "unit_price": st.column_config.NumberColumn("Unit price", format="%.2f"),
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            },
        )

    checks = validate(inv, items, tol)
    status = status_by_invoice(inv, checks)
    vendor_summary = (
        inv.assign(vendor=inv["vendor"].fillna("Unknown")).groupby("vendor", as_index=False)
        .agg(invoices=("id", "count"), subtotal_sum=("subtotal", "sum"),
             tax_sum=("tax", "sum"), total_sum=("total", "sum"))
        .sort_values("total_sum", ascending=False)
    )

    with tab_summary:
        st.dataframe(vendor_summary, hide_index=True, use_container_width=True,
                     column_config={c: money for c in ("subtotal_sum", "tax_sum", "total_sum")})

    with tab_review:
        st.subheader("Checks")
        if checks.empty:
            st.success("All checks passed.")
        else:
            st.dataframe(checks.drop(columns="invoice_id"), hide_index=True, use_container_width=True,
                         column_config={"invoice": "Invoice", "severity": "Severity", "issue": "Issue"})

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Invoices", len(inv))
    m2.metric("Total amount", f"{inv['total'].sum():,.2f}")
    m3.metric("Need review", int((status == "Review").sum()))
    m4.metric("Checks passed", int((status == "OK").sum()))
    if (status == "Review").any():
        st.warning("Some invoices have unresolved checks. You can still export; they are marked 'Review' in the file.")

    st.download_button("Download Excel report", data=build_workbook(inv.assign(status=status), items, checks, vendor_summary),
                       file_name=f"invoices_{datetime.now():%Y%m%d_%H%M}.xlsx", mime=XLSX, type="primary")


# =====================================================================
require_login()
api_key = secret("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY is not configured. Add it to .streamlit/secrets.toml.")
    st.stop()

mode = st.sidebar.radio("Document type", ["Packing lists", "Invoices"], horizontal=True)
st.sidebar.divider()
landing_page.app_bar()
(packing_page if mode == "Packing lists" else invoice_page)(api_key)
