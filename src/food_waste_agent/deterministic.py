from __future__ import annotations
from pathlib import Path
from .semantic import SemanticFrame, normalize_question
from .sql_guard import execute_guarded


def _escape(value: str) -> str:
    return value.replace("'", "''")


def _target_clause(targets: tuple[str, ...]) -> str:
    if not targets:
        return "1=1"
    clauses = []
    for target in targets:
        t = _escape(target.casefold())
        clauses.append(f"lower(Target_Compound) = '{t}'")
    return "(" + " OR ".join(clauses) + ")"


def _material_clause(frame: SemanticFrame) -> str:
    clauses: list[str] = []
    for material in frame.materials:
        m = _escape(material.casefold())
        if material == "brewer's spent grain":
            clauses.append("(lower(Waste_Material) LIKE '%spent grain%' OR lower(Waste_Source) LIKE '%spent grain%' OR lower(Waste_Material) LIKE '%brewer%')")
        elif material == "globe artichoke":
            clauses.append("(lower(Waste_Material) LIKE '%artichoke%' OR lower(Waste_Source) LIKE '%artichoke%')")
        else:
            clauses.append(f"(lower(Waste_Material) LIKE '%{m}%' OR lower(Waste_Source) LIKE '%{m}%')")
    for fraction in frame.fractions:
        f = _escape(fraction.casefold())
        clauses.append(f"lower(Waste_Fraction) LIKE '%{f}%'")
    return " AND ".join(clauses) if clauses else "1=1"


def _method_clauses(frame: SemanticFrame) -> list[str]:
    clauses: list[str] = []
    for method in frame.methods:
        if method == "freeze drying":
            clauses.append("(lower(Extraction_Method) LIKE '%freeze%' OR lower(Extraction_Method) LIKE '%lyophil%')")
        elif method == "ultrasound-assisted extraction":
            clauses.append("(lower(Extraction_Method) LIKE '%ultrasound%' OR lower(Extraction_Method) LIKE '%uae%')")
        elif method == "maceration":
            clauses.append("lower(Extraction_Method) LIKE '%maceration%'")
    return clauses


def _basis_clauses(frame: SemanticFrame) -> list[str]:
    clauses: list[str] = []
    for basis in frame.bases:
        if basis == "dried sample":
            clauses.append("lower(Basis) = 'dried sample'")
        elif basis == "dry":
            clauses.append("(lower(Basis) LIKE '%dry%' OR lower(Basis) LIKE '%dried%' OR lower(Unit) LIKE '%dry%' OR lower(Unit) LIKE '%dried%')")
        elif basis == "wet":
            clauses.append("(lower(Basis) LIKE '%wet%' OR lower(Basis) LIKE '%fresh%')")
    return clauses


def build_sql(frame: SemanticFrame) -> str:
    where = [_target_clause(frame.targets), _material_clause(frame)]
    where += _method_clauses(frame)
    where += _basis_clauses(frame)
    predicate = " AND ".join(f"({x})" for x in where if x)

    if frame.intent == "count":
        return f"SELECT COUNT(*) AS record_count FROM verified_food_waste_records WHERE {predicate};"

    if frame.intent == "source":
        return f"""SELECT Record_ID, Paper_ID, DOI, Source_Location, Source_URL,
        Waste_Source, Target_Compound, Response_Type
        FROM verified_food_waste_records
        WHERE {predicate}
        ORDER BY Record_ID;"""

    if frame.intent == "rank":
        return f"""WITH ranked AS (
          SELECT *, ROW_NUMBER() OVER (
            PARTITION BY Unit, Basis ORDER BY Mean_Value DESC, Record_ID ASC
          ) AS rn
          FROM verified_food_waste_records
          WHERE {predicate} AND Mean_Value IS NOT NULL
        )
        SELECT Record_ID, Paper_ID, DOI, Source_Location, Waste_Source, Waste_Material,
               Waste_Fraction, Target_Compound, Response_Type, Mean_Value, Reported_Value,
               Unit, Basis, Extraction_Method, Temperature_C, Time_min, pH, Solvent
        FROM ranked WHERE rn = 1 ORDER BY Unit, Basis, Record_ID;"""

    return f"""SELECT Record_ID, Paper_ID, DOI, Source_Location, Waste_Source, Waste_Material,
      Waste_Fraction, Data_Record_Type, Target_Compound, Response_Type, Mean_Value,
      Reported_Value, Unit, Basis, Extraction_Method, Temperature_C, Time_min, pH, Solvent
      FROM verified_food_waste_records
      WHERE {predicate}
      ORDER BY Record_ID LIMIT 100;"""


def answer(db_path: str | Path, question: str) -> dict:
    frame = normalize_question(question)
    sql = build_sql(frame)
    rows = execute_guarded(db_path, sql)
    return {"route": "deterministic", "frame": frame.to_dict(), "sql": sql, "rows": rows}
