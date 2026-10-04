# Docpro

Streamlit app that extracts structured data from documents with Google Gemini, checks it, and exports Excel.
Two workflows, each a page in `app.py`:

- **Invoices** (`invoice_page`): extract vendor, number, date, totals and line items, then run consistency checks.
- **Packing lists** (`packing_page`): extract rows, match descriptions to the company item master to get item codes, then check weights and dates.

## Run

```
pip install -r requirements.txt
python -m streamlit run app.py      # or double-click run_app.bat
```

Needs `.streamlit/secrets.toml` (gitignored) with `GEMINI_API_KEY` and `APP_PASSWORD`. Copy `.streamlit/secrets.toml.example`.
Never read, print or commit the real secrets file. There is no test suite yet.

## Layout

| File | Role |
|---|---|
| `app.py` | UI, login gate (`require_login`), both pages, item master sidebar panel |
| `extractor.py` | Gemini calls. Pydantic schemas (`Invoice`, `PackingList`, ...), prompts, `_generate` with retries, `generate_from_text` |
| `matcher.py` | Maps packing-list descriptions to item master codes via Gemini, with a difflib `fallback_match` |
| `packing.py` | Item master load/save (`data/item_master.csv`), code lookup, row assembly, packing validation. Pure pandas |
| `validation.py` | Invoice checks (missing fields, qty x price vs amount, line sum vs subtotal, subtotal + tax vs total, duplicates). Pure pandas |
| `excel_export.py` | Builds styled xlsx workbooks with openpyxl |
| `DEPLOY.md` | Streamlit Community Cloud steps and demo checklist |

## Conventions and gotchas

- Model is set by `MODEL` in `extractor.py` (`models/gemini-3.1-pro-preview`).
- The Gemini SDK rejects a bare `List[...]` schema, so lists are wrapped in a batch model (`InvoiceBatch`, `PackingBatch`, `MatchBatch`).
- Prompts require null for absent fields, never invented values, and dates as `YYYY-MM-DD`.
- Packing lists use day/month/year dates and may use European number format (`1.129,04` = 1129.04). The prompt tells Gemini to convert.
- Validators return a DataFrame with one row per issue. An empty frame means all clear. Status column is `OK` or `Review`.
- `validation.py` and `packing.py` stay free of I/O and Streamlit imports. Keep UI code in `app.py`.
- Uploaded documents are sent to Google Gemini. Only use non-confidential samples for demos.

## Never commit

`.streamlit/secrets.toml`, `data/` (item master), `*.xlsx`, `*.pdf`. `.gitignore` already covers these.
On hosted deployments the disk is temporary, so the saved item master is lost on restart and must be re-uploaded.

## Status

Single commit on `main`, remote `origin`. No known open work was recorded when this file was written.
Add current tasks and decisions below as they come up.

## Open work

- (none recorded)
