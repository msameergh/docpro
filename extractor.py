"""Gemini-based document extraction with strict schemas."""
import time
from typing import List, Optional, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

MODEL = "models/gemini-3.1-pro-preview"

DEFAULT_PROMPT = """You are an accounts-payable data entry specialist.
Extract every invoice or receipt in the attached document. A file may contain several.
Rules:
- Dates must be formatted YYYY-MM-DD.
- Numbers must be plain numerics: no currency symbols, no thousands separators.
- currency is the 3-letter ISO code (e.g. USD, EUR, INR) if it can be determined.
- Include every line item exactly as printed. Do not invent values; use null when a field is absent.
- subtotal is the amount before tax; tax is the total tax amount; total is the final amount due."""


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = Field(None, description="Line total as printed")


class Invoice(BaseModel):
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    line_items: List[LineItem] = Field(default_factory=list)


class InvoiceBatch(BaseModel):
    """Top-level wrapper: the Gemini SDK rejects a bare List[...] schema."""
    invoices: List[Invoice] = Field(default_factory=list)


PACKING_PROMPT = """You are a logistics data entry specialist.
Extract every line of the packing list in the attached document. A file may contain several packing lists.
Rules:
- Return one entry per printed table row (same product on different production dates = separate entries).
- description: the full product description for that row, joined into one line. If a row has a separate
  item/product code column, put it in item_code, otherwise leave item_code null. Never invent a code.
- production_date and expiry_date: format YYYY-MM-DD. The document uses day/month/year order.
- cartons: number of cartons/boxes (whole number).
- net_weight_kg and gross_weight_kg: plain numbers. The document may use European format where
  '.' is the thousands separator and ',' the decimal mark (e.g. '1.129,04' means 1129.04). Convert correctly.
- Do NOT include total or subtotal rows, headers or footers as lines.
- document_number is the packing list number (e.g. 'NR.' or 'No.'), document_date its date (YYYY-MM-DD)."""


class PackingLine(BaseModel):
    item_code: Optional[str] = None
    description: Optional[str] = None
    production_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    expiry_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    cartons: Optional[float] = None
    net_weight_kg: Optional[float] = None
    gross_weight_kg: Optional[float] = None


class PackingList(BaseModel):
    document_number: Optional[str] = None
    document_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    order_reference: Optional[str] = None
    consignee: Optional[str] = None
    lines: List[PackingLine] = Field(default_factory=list)


class PackingBatch(BaseModel):
    packing_lists: List[PackingList] = Field(default_factory=list)


T = TypeVar("T", bound=BaseModel)


def _generate(api_key: str, parts: list, schema: Type[T], retries: int = 2) -> T:
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=65536,
        thinking_config=types.ThinkingConfig(thinking_level="low"),
        response_mime_type="application/json",
        response_schema=schema,
    )
    contents = [types.Content(role="user", parts=parts)]
    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
            if resp.parsed is None:
                raise ValueError("Model returned no parseable data")
            return resp.parsed
        except Exception as e:  # network / rate limit / bad JSON: retry with backoff
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise last_err


def _extract(api_key: str, file_bytes: bytes, mime_type: str, prompt: str, schema: Type[T],
             retries: int = 2) -> T:
    parts = [types.Part.from_bytes(data=file_bytes, mime_type=mime_type), types.Part.from_text(text=prompt)]
    return _generate(api_key, parts, schema, retries)


def generate_from_text(api_key: str, prompt: str, schema: Type[T]) -> T:
    return _generate(api_key, [types.Part.from_text(text=prompt)], schema)


def extract_invoices(api_key: str, file_bytes: bytes, mime_type: str, prompt: str = DEFAULT_PROMPT) -> List[Invoice]:
    return list(_extract(api_key, file_bytes, mime_type, prompt, InvoiceBatch).invoices)


def extract_packing_lists(api_key: str, file_bytes: bytes, mime_type: str,
                          prompt: str = PACKING_PROMPT) -> List[PackingList]:
    return list(_extract(api_key, file_bytes, mime_type, prompt, PackingBatch).packing_lists)
