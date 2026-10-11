from pathlib import Path
import os
import sys
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from food_waste_agent.config import settings
from food_waste_agent.database import database_stats
from food_waste_agent.agent import HybridEvidenceAgent

st.set_page_config(page_title="Food-Waste Evidence Agent", page_icon="♻️", layout="wide")
st.title("♻️ Food-Waste Evidence Agent")
st.caption("Verified SQLite evidence + semantic normalization + hybrid routing + guarded optional LLM-to-SQL.")

stats = database_stats(settings.db_path)
cols = st.columns(5)
for c, (k, v) in zip(cols, stats.items()):
    c.metric(k.replace("_", " ").title(), v)

question = st.text_input("Ask the database", "Which clementine rind conditions produced the highest pectin yield?")
allow_llm = st.toggle("Allow optional guarded LLM-to-SQL", value=False, disabled=not bool(os.getenv("OPENAI_API_KEY")))
summarize = st.toggle("Generate grounded LLM summary", value=False, disabled=not bool(os.getenv("OPENAI_API_KEY")))

if st.button("Run", type="primary"):
    result = HybridEvidenceAgent(settings.db_path, settings.openai_model).ask(question, allow_llm, summarize)
    st.write(f"**Route:** {result['route']}")
    st.json(result["frame"])
    if result.get("sql"):
        with st.expander("SQL"):
            st.code(result["sql"], language="sql")
    st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True)
    if result.get("summary"):
        st.markdown(result["summary"])
    if result.get("citations"):
        st.write("**Evidence citations**")
        for citation in result["citations"]:
            st.write("- " + citation)
