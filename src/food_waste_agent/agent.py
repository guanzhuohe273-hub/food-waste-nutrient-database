from __future__ import annotations
from pathlib import Path
import os
from .semantic import normalize_question
from .deterministic import answer as deterministic_answer
from .retrieval import retrieve_evidence, format_citations
from .sql_guard import execute_guarded
from .llm import generate_sql, grounded_summary


class HybridEvidenceAgent:
    """Local-first hybrid agent with deterministic, guarded SQL and evidence retrieval tools."""

    def __init__(self, db_path: str | Path, model: str = "gpt-5-mini"):
        self.db_path = Path(db_path)
        self.model = model

    def ask(self, question: str, allow_llm: bool = False, summarize: bool = False) -> dict:
        frame = normalize_question(question)

        if frame.confidence >= 0.55 and (frame.targets or frame.materials or frame.fractions or frame.bases):
            result = deterministic_answer(self.db_path, question)
            if result["rows"]:
                result["citations"] = format_citations(result["rows"])
                if summarize and allow_llm and os.getenv("OPENAI_API_KEY"):
                    result["summary"] = grounded_summary(question, result["rows"], self.model)
                return result

        if allow_llm and os.getenv("OPENAI_API_KEY"):
            sql = generate_sql(frame.normalized, self.model)
            rows = execute_guarded(self.db_path, sql)
            result = {
                "route": "guarded_llm_sql",
                "frame": frame.to_dict(),
                "sql": sql,
                "rows": rows,
                "citations": format_citations(rows),
            }
            if summarize and rows:
                result["summary"] = grounded_summary(question, rows, self.model)
            return result

        rows = retrieve_evidence(self.db_path, frame.normalized, k=8)
        return {
            "route": "evidence_retrieval",
            "frame": frame.to_dict(),
            "rows": rows,
            "citations": format_citations(rows),
            "summary": None,
        }
