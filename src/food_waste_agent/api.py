from __future__ import annotations
from fastapi import FastAPI, Query
from .config import settings
from .database import database_stats
from .agent import HybridEvidenceAgent

app = FastAPI(title="Food-Waste Evidence Agent", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", **database_stats(settings.db_path)}

@app.get("/ask")
def ask(question: str = Query(min_length=2), allow_llm: bool = False, summarize: bool = False):
    agent = HybridEvidenceAgent(settings.db_path, settings.openai_model)
    return agent.ask(question, allow_llm=allow_llm, summarize=summarize)
