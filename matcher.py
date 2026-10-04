"""Match packing-list descriptions to the item master using Gemini.

The supplier's wording and the company's master wording differ (abbreviations, word order,
pack notation), so plain text similarity is not enough.
"""
import difflib
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field

from extractor import generate_from_text

CHUNK = 40          # document descriptions per request
FULL_MASTER_MAX = 800   # send the whole master up to this size, else pre-filter candidates
CANDIDATES_PER_DESC = 40

PROMPT = """You map product descriptions from a supplier's packing list to the buyer's item master.
The wording differs: the master uses abbreviations (GRLR=griller/whole chicken, FRZN=frozen,
AI=Al Islami brand, BL SL=boneless skinless, CHCKN/CHK=chicken, TP OFF=top off, SPCL OFF=special offer,
gm/G=grams, KG=kilograms) and pack notation like 1X12X900G (cartons x packs x pack size).

For each numbered DOCUMENT item choose the single best ITEM MASTER entry.
Match on, in order: product type and cut (e.g. drumstick, liver, whole leg, half breast boneless skinless,
gizzard), brand, pack size and carton configuration (e.g. '900G X 12 = 10.80 KG' means 12 packs of 900g
per carton), then other attributes.
Rules:
- Prefer the standard variant. Only pick PROMO, CAMPAIGN, RAMADAN, SPCL OFF, TP OFF, OFF or similar
  special variants if the document text itself indicates that variant.
- If several master entries fit equally well, pick the most standard one and set confidence to Medium or Low.
- item_code must be copied exactly from the master list. If nothing fits, use null with confidence Low.
- confidence: High = clearly the same product and pack; Medium = likely; Low = guess or none.
- reason: one short sentence."""


class Match(BaseModel):
    index: int = Field(description="Number of the document item")
    item_code: Optional[str] = None
    confidence: Optional[str] = Field(None, description="High, Medium or Low")
    reason: Optional[str] = None


class MatchBatch(BaseModel):
    matches: List[Match] = Field(default_factory=list)


def _tokens(s: str) -> set:
    return set(re.findall(r"[A-Z0-9]+", str(s).upper()))


def _candidates(descs: List[str], master: pd.DataFrame) -> pd.DataFrame:
    """Narrow a large master to plausible rows for these descriptions."""
    if len(master) <= FULL_MASTER_MAX:
        return master
    mt = [_tokens(d) for d in master["item_description"]]
    keep = set()
    for d in descs:
        dt = _tokens(d)
        scores = [(len(dt & t) / (len(dt | t) or 1), i) for i, t in enumerate(mt)]
        scores.sort(reverse=True)
        keep.update(i for _, i in scores[:CANDIDATES_PER_DESC])
    return master.iloc[sorted(keep)]


def match_descriptions(api_key: str, descriptions: List[str], master: pd.DataFrame
                       ) -> Dict[str, Tuple[Optional[str], str, str]]:
    """Return {document description: (item_code or None, confidence, reason)}."""
    result: Dict[str, Tuple[Optional[str], str, str]] = {}
    if master.empty:
        return {d: (None, "Not found", "No item master loaded") for d in descriptions}
    valid = set(master["item_code"].astype(str))
    unique = list(dict.fromkeys(d for d in descriptions if d))

    for start in range(0, len(unique), CHUNK):
        chunk = unique[start:start + CHUNK]
        cand = _candidates(chunk, master)
        master_txt = "\n".join(f"{c} | {d}" for c, d in zip(cand["item_code"], cand["item_description"]))
        docs_txt = "\n".join(f"{i}. {d}" for i, d in enumerate(chunk, start=1))
        prompt = f"{PROMPT}\n\nITEM MASTER (code | description):\n{master_txt}\n\nDOCUMENT ITEMS:\n{docs_txt}"
        batch = generate_from_text(api_key, prompt, MatchBatch)
        for m in batch.matches:
            if not (1 <= m.index <= len(chunk)):
                continue
            code = str(m.item_code).strip() if m.item_code else None
            conf = (m.confidence or "Low").capitalize()
            if code not in valid:  # model must not invent codes
                code, conf = None, "Low"
            result[chunk[m.index - 1]] = (code, conf if code else "Not found", m.reason or "")
    for d in unique:
        result.setdefault(d, (None, "Not found", "No match returned"))
    return result


def fallback_match(descriptions: List[str], master: pd.DataFrame) -> Dict[str, Tuple[Optional[str], str, str]]:
    """Offline text-similarity fallback used only if the AI call fails."""
    keys = {re.sub(r"[^A-Z0-9]+", " ", d.upper()).strip(): c
            for d, c in zip(master["item_description"], master["item_code"])}
    out = {}
    for d in dict.fromkeys(x for x in descriptions if x):
        n = re.sub(r"[^A-Z0-9]+", " ", d.upper()).strip()
        close = difflib.get_close_matches(n, list(keys), n=1, cutoff=0.8) if keys else []
        out[d] = (keys[close[0]], "Low", "Text similarity only (AI matching unavailable)") if close \
            else (None, "Not found", "")
    return out
