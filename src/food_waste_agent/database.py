from __future__ import annotations
from pathlib import Path
import base64
import gzip
import io
import sqlite3
import pandas as pd


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.where(pd.notna(frame), None)


def load_verified_records(project_root: str | Path) -> pd.DataFrame:
    root = Path(project_root)
    csv_path = root / "data" / "verified_records.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)

    parts = sorted((root / "data").glob("records_part_*.b64"))
    if not parts:
        raise FileNotFoundError("No verified-record source found")
    payload = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    raw = gzip.decompress(base64.b64decode(payload))
    return pd.read_csv(io.BytesIO(raw))


def _derive_papers(records: pd.DataFrame) -> pd.DataFrame:
    cols = ["Paper_ID", "Publication_Year", "DOI", "Source_URL"]
    return records[cols].drop_duplicates(subset=["Paper_ID"]).sort_values("Paper_ID").reset_index(drop=True)


def _derive_experiments(records: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Experiment_ID", "Paper_ID", "Waste_Source", "Data_Record_Type", "Extraction_Method",
        "Temperature_C", "Time_min", "pH", "Solvent", "Solid_Liquid_Ratio", "Particle_Size_mm",
        "Ultrasound_Frequency_kHz", "Ultrasound_Power_W", "Agitation_rpm", "Source_Location",
    ]
    return records[cols].drop_duplicates(subset=["Experiment_ID"]).sort_values("Experiment_ID").reset_index(drop=True)


def build_sqlite(records: pd.DataFrame, db_path: str | Path) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    records = _clean(records)
    papers = _clean(_derive_papers(records))
    experiments = _clean(_derive_experiments(records))

    with sqlite3.connect(db_path) as conn:
        papers.to_sql("papers", conn, index=False, if_exists="replace")
        experiments.to_sql("experiments", conn, index=False, if_exists="replace")
        records.to_sql("nutrient_records", conn, index=False, if_exists="replace")
        records.to_sql("food_waste_records", conn, index=False, if_exists="replace")
        conn.executescript("""
        CREATE INDEX idx_records_target ON nutrient_records(Target_Compound);
        CREATE INDEX idx_records_waste ON nutrient_records(Waste_Material, Waste_Fraction);
        CREATE INDEX idx_records_paper ON nutrient_records(Paper_ID);
        CREATE INDEX idx_records_record_type ON nutrient_records(Data_Record_Type);

        DROP VIEW IF EXISTS verified_food_waste_records;
        CREATE VIEW verified_food_waste_records AS
        SELECT * FROM nutrient_records WHERE Student_Final_Check = 'Checked';

        DROP VIEW IF EXISTS compatibility_records;
        CREATE VIEW compatibility_records AS
        SELECT *, COALESCE(Unit, '') || ' | ' || COALESCE(Basis, '') AS Compatibility_Group
        FROM verified_food_waste_records;
        """)
        conn.commit()
    return db_path


def build_from_project(project_root: str | Path, db_path: str | Path | None = None) -> Path:
    root = Path(project_root)
    db_path = Path(db_path) if db_path else root / "data" / "food_waste.db"
    return build_sqlite(load_verified_records(root), db_path)


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path).resolve()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def database_stats(db_path: str | Path) -> dict:
    with connect_readonly(db_path) as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS records,
                   COUNT(DISTINCT Paper_ID) AS papers,
                   COUNT(DISTINCT Experiment_ID) AS experiments,
                   COUNT(DISTINCT Waste_Source) AS waste_sources,
                   COUNT(DISTINCT Target_Compound) AS targets
            FROM verified_food_waste_records
        """).fetchone()
    return dict(row)
