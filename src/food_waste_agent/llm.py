from __future__ import annotations
import json
import os

SCHEMA = """
Allowed SQLite objects:
- verified_food_waste_records: verified evidence rows
- compatibility_records: verified rows plus Compatibility_Group
- papers: bibliographic metadata
- experiments: experiment conditions

Important semantics:
- Waste_Material is the material name; Waste_Fraction stores peel, stem, leaf, seed, etc.
- Protein, Protein content and Protein recovery are distinct meanings.
- Total dietary fibre and Soluble dietary fibre are distinct targets.
- Never rank across incompatible Unit/Basis groups.
- British 'fibre' is used in stored target labels even when users write 'fiber'.
"""


def _client(api_key: str | None = None):
    from openai import OpenAI
    return OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))


def generate_sql(question: str, model: str = "gpt-5-mini", api_key: str | None = None) -> str:
    prompt = f"""Translate the question into one safe SQLite SELECT query.
Return SQL only, no markdown. Respect all semantics below.
{SCHEMA}
Question: {question}
"""
    response = _client(api_key).responses.create(model=model, input=prompt)
    text = response.output_text.strip().strip("`")
    if text.lower().startswith("sql\n"):
        text = text[4:]
    return text


def grounded_summary(question: str, rows: list[dict], model: str = "gpt-5-mini", api_key: str | None = None) -> str:
    evidence = json.dumps(rows[:12], ensure_ascii=False, default=str)
    prompt = f"""Answer only from the evidence JSON.
Never invent a value or citation. Keep incompatible Unit/Basis groups separate.
Cite Record_ID and DOI. If evidence is insufficient, say so.

Question: {question}
Evidence: {evidence}
"""
    return _client(api_key).responses.create(model=model, input=prompt).output_text.strip()
