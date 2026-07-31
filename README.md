# Food-Waste Nutrient & Extraction Database

A Streamlit prototype for exploring literature-derived food-waste nutrient composition and extraction data.

## Current dataset

- 408 records
- 6 peer-reviewed source papers
- 36 waste sources
- 211 experiment groups
- 228 composition records
- 180 extraction/result records
- 408 records marked as manually checked against their original sources

## Features

- Dashboard summaries by paper and record type
- Structured filtering by waste source, target compound and extraction method
- Natural-language database interrogation
- Unit/basis compatibility grouping to avoid invalid mixed-unit rankings
- Traceable evidence using Record IDs and DOIs
- Explicit no-evidence responses for unsupported questions
- Optional OpenAI evidence summarisation; the core app works without an API key

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy with Streamlit Community Cloud

Select this repository and use:

```text
Main file path: streamlit_app.py
Branch: main
```

## Scientific interpretation

Composition records and extraction records represent different response types and should not be treated as interchangeable. Numerical comparisons should only be made within compatible unit and measurement-basis groups.
