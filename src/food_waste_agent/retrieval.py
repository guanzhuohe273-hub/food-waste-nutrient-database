from __future__ import annotations
from pathlib import Path
import re
from .database import connect_readonly
from .semantic import normalize_question

TEXT_FIELDS = [
    "Waste_Source", "Waste_Material", "Waste_Fraction", "Target_Compound", "Compound_Group",
    "Response_Type", "Extraction_Method", "Sample_Preparation", "Basis", "Confidence_Notes",
    "Potential_Application", "Source_Location"
]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\w'-]+", text.casefold()) if len(t) > 1}


def retrieve_evidence(db_path: str | Path, question: str, k: int = 8) -> list[dict]:
    frame = normalize_question(question)
    q_tokens = _tokens(frame.normalized)
    with connect_readonly(db_path) as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM verified_food_waste_records").fetchall()]

    scored = []
    for row in rows:
        doc = " ".join(str(row.get(f) or "") for f in TEXT_FIELDS)
        score = len(q_tokens & _tokens(doc))
        if row.get("Target_Compound") and str(row["Target_Compound"]).casefold() in frame.targets:
            score += 5
        for m in frame.materials:
            if m.casefold() in (str(row.get("Waste_Material") or "") + " " + str(row.get("Waste_Source") or "")).casefold():
                score += 2
        for f in frame.fractions:
            if f.casefold() in str(row.get("Waste_Fraction") or "").casefold():
                score += 2
        if score:
            scored.append((score, str(row.get("Record_ID")), row))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [r for _, _, r in scored[:k]]


def format_citations(rows: list[dict]) -> list[str]:
    citations = []
    seen = set()
    for row in rows:
        key = (row.get("Record_ID"), row.get("DOI"))
        if key in seen:
            continue
        seen.add(key)
        citations.append(f"{row.get('Record_ID')} | DOI: {row.get('DOI')} | {row.get('Source_Location')}")
    return citations
