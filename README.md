# Food-Waste Evidence Agent

An evidence-grounded AI application developed from a 2026 MSc dissertation in Computer Systems Engineering at the University of Glasgow. The project combines a **verified SQLite evidence base**, **deterministic natural-language-to-SQL**, an optional **guarded LLM-to-SQL** path, **semantic normalization**, **hybrid routing**, **local evidence retrieval**, **FastAPI**, **Streamlit**, automated tests, and CI.

> The semantic normalizer and hybrid router are post-dissertation engineering extensions. Historical dissertation benchmark results are preserved separately and are not relabelled as results of the extension.

## Why this project exists

Scientific values that look comparable often are not. Food-waste studies report composition, extracted content, recovery/yield, different units, and different measurement bases. This project keeps provenance and semantics attached to every value instead of flattening them into one misleading number.

## Verified data

- **408** manually checked records
- **6** peer-reviewed source studies
- **211** experiment contexts
- **36** waste sources
- **19** target compounds
- Record-level `Record_ID`, DOI, and source location
- Verified records bundled losslessly as compressed reproducibility chunks (`data/records_part_*.b64`)
- Original units and measurement bases preserved

## Historical dissertation evaluation

| System | Canonical exact | Robustness exact |
|---|---:|---:|
| Deterministic baseline | **40/40 (100.0%)** | **21/40 (52.5%)** |
| Guarded GPT-5-mini | **29/40 (72.5%)** | **21/40 (52.5%)** |

Additional results:

- Guarded LLM SQL executed safely in **80/80** formal cases.
- Offline SQL-safety suite passed **26/26** cases.
- Robustness analysis showed complementary coverage between deterministic and LLM paths.
- Failure analysis identified semantic/schema-linking errors as a larger problem than SQL syntax.

## v1.0 engineering extension

### Semantic normalization

Maps domain variants into controlled concepts before querying, for example:

- `rind / skin -> peel`
- `fiber -> fibre`
- `TPC -> Total phenolic content`
- `BSG -> brewer's spent grain`
- separate `Protein`, `Protein content`, and `Protein recovery`
- freeze-dried / lyophilized -> freeze-drying semantics

### Confidence-routed agent

High-confidence controlled-domain questions use deterministic querying first. Ambiguous requests can optionally use LLM-to-SQL, while a local evidence retriever provides an API-free fallback.

### Guarded SQL execution

Generated SQL never gets direct database authority. Queries must be a single `SELECT`/`WITH` statement, use allow-listed objects, and execute against read-only SQLite under an authorizer, row cap, and execution-step limit.

### Evidence traceability

Results preserve `Record_ID`, DOI, source location, unit, and measurement basis. Optional grounded summaries receive retrieved evidence only.

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e ".[dev]"
python scripts/build_database.py
pytest -q
# Optional: materialize the source CSV
python scripts/export_records.py
```

Run the API:

```bash
uvicorn food_waste_agent.api:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Run the UI:

```bash
pip install -e ".[ui]"
streamlit run app/streamlit_app.py
```

Optional LLM path:

```bash
pip install -e ".[llm]"
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5-mini"
```

The deterministic and retrieval paths work without an API key.

## Example

```python
from food_waste_agent.agent import HybridEvidenceAgent

agent = HybridEvidenceAgent("data/food_waste.db")
result = agent.ask("Which clementine rind conditions produced the highest pectin yield?")
print(result["route"])
print(result["rows"])
print(result["citations"])
```

## Reproducibility and claims

The frozen dissertation benchmark is historical evidence. The post-dissertation extension must not be described as having improved held-out accuracy unless a new benchmark is frozen before further tuning.

See:

- [`docs/evaluation.md`](docs/evaluation.md)
- [`docs/data_provenance.md`](docs/data_provenance.md)
- [`docs/limitations.md`](docs/limitations.md)
- [`benchmarks/README.md`](benchmarks/README.md)

## Tech stack

Python · SQLite · Pandas · FastAPI · Streamlit · OpenAI API (optional) · pytest · GitHub Actions

## Data and publication note

The repository contains the verified structured dataset and bibliographic metadata, but does not redistribute the original source-paper PDFs.

## License

No license is granted by default. Add a license only when you want to define reuse rights explicitly.
