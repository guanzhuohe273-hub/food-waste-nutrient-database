import os
import base64
import gzip
import io
import pandas as pd
import streamlit as st
import altair as alt

from query_engine import (
    local_answer,
    retrieve,
    compatibility_groups,
)
from data_blob import DATA_B64

st.set_page_config(
    page_title="Food-Waste Nutrient Database",
    page_icon="♻️",
    layout="wide",
)

@st.cache_data
def get_records():
    raw = gzip.decompress(base64.b64decode(DATA_B64))
    return pd.read_csv(io.BytesIO(raw))

df = get_records()

st.title("♻️ Food-Waste Nutrient & Extraction Database")
st.caption(
    "Literature-derived prototype. Original units and measurement bases are preserved; "
    "records are compared only within compatible unit/basis groups."
)

with st.sidebar:
    st.header("Database")
    st.metric("Records", f"{len(df):,}")
    st.metric("Source papers", df["Paper_ID"].nunique())
    st.metric("Experiments", df["Experiment_ID"].nunique())
    st.divider()

    record_types = st.multiselect(
        "Record type",
        sorted(df["Data_Record_Type"].dropna().unique()),
        default=sorted(df["Data_Record_Type"].dropna().unique()),
    )
    selected_papers = st.multiselect(
        "Source paper",
        sorted(df["Paper_ID"].dropna().unique()),
        default=sorted(df["Paper_ID"].dropna().unique()),
    )

base = df[
    df["Data_Record_Type"].isin(record_types)
    & df["Paper_ID"].isin(selected_papers)
].copy()

tab1, tab2, tab3, tab4 = st.tabs(
    ["Dashboard", "Search & filter", "Ask the database", "Sources & quality"]
)

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Visible records", f"{len(base):,}")
    c2.metric("Waste sources", base["Waste_Source"].nunique())
    c3.metric("Target compounds", base["Target_Compound"].nunique())
    c4.metric("Pending checks", int((base["Student_Final_Check"] == "Pending").sum()))

    left, right = st.columns(2)

    source_counts = (
        base.groupby("Paper_ID")
        .size()
        .reset_index(name="Records")
        .sort_values("Paper_ID")
    )
    source_chart = (
        alt.Chart(source_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "Paper_ID:N",
                title=None,
                sort=None,
                axis=alt.Axis(labelAngle=0, labelOverlap=False),
            ),
            y=alt.Y("Records:Q", title="Records"),
            tooltip=["Paper_ID:N", "Records:Q"],
        )
        .properties(height=330)
    )

    type_counts = (
        base.groupby("Data_Record_Type")
        .size()
        .reset_index(name="Records")
    )
    type_chart = (
        alt.Chart(type_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "Data_Record_Type:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelAngle=0,
                    labelLimit=180,
                    labelOverlap=False,
                ),
            ),
            y=alt.Y("Records:Q", title="Records"),
            tooltip=["Data_Record_Type:N", "Records:Q"],
        )
        .properties(height=330)
    )

    with left:
        st.subheader("Records by source")
        st.altair_chart(source_chart, use_container_width=True)
    with right:
        st.subheader("Records by type")
        st.altair_chart(type_chart, use_container_width=True)

    st.info(
        "Composition records describe what is present in a material. Extraction records describe "
        "what was recovered under specified conditions. These record types are not interchangeable."
    )

with tab2:
    st.subheader("Structured search")
    f1, f2, f3 = st.columns(3)
    waste_sel = f1.multiselect("Waste source", sorted(base["Waste_Source"].dropna().unique()))
    target_sel = f2.multiselect("Target compound", sorted(base["Target_Compound"].dropna().unique()))
    method_sel = f3.multiselect("Extraction method", sorted(base["Extraction_Method"].dropna().unique()))

    filtered = base.copy()
    if waste_sel:
        filtered = filtered[filtered["Waste_Source"].isin(waste_sel)]
    if target_sel:
        filtered = filtered[filtered["Target_Compound"].isin(target_sel)]
    if method_sel:
        filtered = filtered[filtered["Extraction_Method"].isin(method_sel)]

    show_cols = [
        "Record_ID","Paper_ID","Waste_Source","Data_Record_Type","Target_Compound",
        "Response_Type","Reported_Value","Unit","Basis","Extraction_Method",
        "Temperature_C","Time_min","pH","Solvent","Source_Location","DOI",
        "Student_Final_Check"
    ]
    st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="food_waste_filtered.csv",
        mime="text/csv",
    )

def ai_answer(question: str, evidence: pd.DataFrame, api_key: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    cols = [
        "Record_ID","Paper_ID","Waste_Source","Target_Compound","Response_Type",
        "Reported_Value","Unit","Basis","Extraction_Method","Temperature_C",
        "Time_min","pH","Solvent","DOI","Confidence_Notes"
    ]
    evidence_text = evidence[cols].to_csv(index=False)
    prompt = f"""
Answer the user question using only the database evidence below.

Rules:
- Never invent values, conditions or citations.
- Keep incompatible unit/basis groups separate.
- Distinguish composition from extraction yield.
- Cite Record_ID and DOI values.
- State when the evidence is insufficient.

Question:
{question}

Evidence:
{evidence_text}
"""
    response = client.responses.create(model=model, input=prompt)
    return response.output_text

with tab3:
    st.subheader("Natural-language interrogation")
    question = st.text_input(
        "Ask a question",
        placeholder="Which clementine-peel conditions gave the highest pectin yield?"
    )
    use_ai = st.toggle("Use optional OpenAI evidence summary", value=False)
    api_key = ""
    model = os.getenv("OPENAI_MODEL", "gpt-5")

    if use_ai:
        api_key = st.text_input(
            "OpenAI API key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
        )
        model = st.text_input("Model", value=model)

    if st.button("Run query", type="primary") and question:
        answer, evidence, plan = local_answer(question, base)
        st.write("**Query interpretation**")
        st.json(plan.to_dict())
        st.write("**Local evidence answer**")
        st.markdown(answer)

        if not evidence.empty:
            st.write("**Compatibility groups**")
            st.dataframe(compatibility_groups(evidence), hide_index=True)
            display_cols = [
                "Record_ID","Paper_ID","Waste_Source","Target_Compound","Response_Type",
                "Reported_Value","Unit","Basis","Extraction_Method","Temperature_C",
                "Time_min","pH","DOI"
            ]
            st.dataframe(evidence[display_cols], use_container_width=True, hide_index=True)

        if use_ai:
            if not api_key:
                st.error("Enter an API key or set OPENAI_API_KEY.")
            elif evidence.empty:
                st.warning("AI mode was not called because no database evidence was retrieved.")
            else:
                try:
                    with st.spinner("Generating a grounded evidence summary..."):
                        st.markdown(ai_answer(question, evidence, api_key, model))
                except Exception as exc:
                    st.error(f"AI request failed: {exc}")

with tab4:
    st.subheader("Quality workflow")
    quality = (
        df.groupby(["Verification_Status","Student_Final_Check"])
          .size()
          .reset_index(name="Records")
    )
    st.dataframe(quality, use_container_width=True, hide_index=True)
    checked_count = int((df["Student_Final_Check"] == "Checked").sum())
    pending_count = int((df["Student_Final_Check"] == "Pending").sum())
    if checked_count:
        st.success(
            f"{checked_count} record(s) have completed final student verification; "
            f"{pending_count} record(s) remain Pending."
        )
    if pending_count:
        st.warning(
            "Pending records must be checked against their original source rows before "
            "the complete dataset is described as fully manually verified."
        )
