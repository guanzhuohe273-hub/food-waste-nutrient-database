from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import pandas as pd


TARGET_ALIASES = {
    "calcium": "Calcium", "钙": "Calcium",
    "phosphorus": "Phosphorus", "磷": "Phosphorus",
    "protein": "Protein", "蛋白": "Protein",
    "protein recovery": "Protein recovery", "蛋白回收": "Protein recovery",
    "protein content": "Protein content", "蛋白含量": "Protein content",
    "pectin": "Pectin", "果胶": "Pectin",
    "phenolic": "Total phenolic content", "polyphenol": "Total phenolic content",
    "多酚": "Total phenolic content",
    "flavonoid": "Total flavonoid content", "黄酮": "Total flavonoid content",
    "dietary fibre": "Total dietary fibre", "dietary fiber": "Total dietary fibre",
    "fibre": "Total dietary fibre", "fiber": "Total dietary fibre",
    "膳食纤维": "Total dietary fibre",
    "lipid": "Lipids", "fat": "Lipids", "脂肪": "Lipids",
    "potassium": "Potassium", "钾": "Potassium",
    "magnesium": "Magnesium", "镁": "Magnesium",
    "sodium": "Sodium", "钠": "Sodium",
    "zinc": "Zinc", "锌": "Zinc",
    "iron": "Iron", "铁": "Iron",
    "vitamin b12": "Vitamin B12", "维生素b12": "Vitamin B12",
}

EXTRACTION_TERMS = {
    "extract", "extraction", "yield", "recover", "recovery", "method",
    "condition", "temperature", "solvent", "提取", "回收", "产率", "方法", "条件"
}

RANK_TERMS = {
    "highest", "most", "best", "rich", "maximum", "top",
    "最高", "最多", "最丰富", "最佳", "排名"
}

COMPARE_TERMS = {"compare", "comparison", "versus", " vs ", "比较", "对比"}


@dataclass(frozen=True)
class QueryPlan:
    targets: tuple[str, ...]
    wastes: tuple[str, ...]
    methods: tuple[str, ...]
    extraction_intent: bool
    rank_intent: bool
    compare_intent: bool

    def to_dict(self) -> dict:
        return asdict(self)


def load_records(data_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(data_path)


def _find_options(question: str, options: Iterable[str]) -> list[str]:
    q = question.casefold()
    matches = []
    for option in sorted(set(options), key=lambda x: len(str(x)), reverse=True):
        if str(option).casefold() in q:
            matches.append(str(option))
    return matches


def detect_query(question: str, frame: pd.DataFrame) -> QueryPlan:
    q = f" {question.casefold()} "

    targets = []
    for alias, canonical in sorted(TARGET_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias.casefold() in q and canonical not in targets:
            targets.append(canonical)

    wastes = _find_options(question, frame["Waste_Source"].dropna().astype(str).unique())
    methods = _find_options(question, frame["Extraction_Method"].dropna().astype(str).unique())

    extraction_intent = any(term in q for term in EXTRACTION_TERMS)
    rank_intent = any(term in q for term in RANK_TERMS)
    compare_intent = any(term in q for term in COMPARE_TERMS)

    return QueryPlan(
        targets=tuple(targets),
        wastes=tuple(wastes),
        methods=tuple(methods),
        extraction_intent=extraction_intent,
        rank_intent=rank_intent,
        compare_intent=compare_intent,
    )


def retrieve(question: str, frame: pd.DataFrame, limit: int = 200) -> tuple[pd.DataFrame, QueryPlan]:
    plan = detect_query(question, frame)
    result = frame.copy()

    if plan.targets:
        target_mask = result["Target_Compound"].isin(plan.targets)
        if "Protein" in plan.targets:
            target_mask = target_mask | result["Target_Compound"].isin(["Protein recovery", "Protein content"])
        result = result[target_mask]

    if plan.wastes:
        result = result[result["Waste_Source"].isin(plan.wastes)]

    if plan.methods:
        result = result[result["Extraction_Method"].isin(plan.methods)]

    if plan.extraction_intent:
        result = result[result["Data_Record_Type"] != "Composition"]

    if plan.rank_intent:
        result = result.sort_values(
            ["Unit", "Basis", "Mean_Value"],
            ascending=[True, True, False],
            na_position="last",
        )
    else:
        result = result.sort_values(["Paper_ID", "Record_ID"])

    return result.head(limit).reset_index(drop=True), plan


def compatibility_groups(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Unit", "Basis", "Records"])
    return (
        frame.groupby(["Unit", "Basis"], dropna=False)
        .size()
        .reset_index(name="Records")
        .sort_values(["Unit", "Basis"])
        .reset_index(drop=True)
    )


def local_answer(question: str, frame: pd.DataFrame, max_groups: int = 6, top_n: int = 3) -> tuple[str, pd.DataFrame, QueryPlan]:
    result, plan = retrieve(question, frame)
    if result.empty:
        return "No matching evidence was found in the current database.", result, plan

    lines = [f"Retrieved {len(result)} matching record(s)."]
    if plan.targets:
        lines.append("Detected target: " + ", ".join(plan.targets))
    if plan.wastes:
        lines.append("Detected waste source: " + ", ".join(plan.wastes))
    if plan.methods:
        lines.append("Detected method: " + ", ".join(plan.methods))

    grouped = list(result.groupby(["Unit", "Basis"], dropna=False))
    if len(grouped) > 1:
        lines.append(
            "The evidence contains multiple unit/basis groups. "
            "They are reported separately and are not combined into one ranking."
        )

    for (unit, basis), group in grouped[:max_groups]:
        lines.append(f"\nComparison group: {unit} | {basis}")
        numeric = group.dropna(subset=["Mean_Value"]).sort_values("Mean_Value", ascending=False)
        top = numeric.head(top_n) if not numeric.empty else group.head(top_n)
        for _, row in top.iterrows():
            condition_parts = []
            for label, col, suffix in [
                ("T", "Temperature_C", "°C"),
                ("time", "Time_min", " min"),
                ("pH", "pH", ""),
            ]:
                value = row.get(col)
                if pd.notna(value):
                    condition_parts.append(f"{label}={value:g}{suffix}")
            condition = "; ".join(condition_parts)
            if condition:
                condition = f"; {condition}"
            lines.append(
                f"- {row['Waste_Source']}: {row['Reported_Value']} {row['Unit']} "
                f"({row['Response_Type']}{condition}; {row['Record_ID']}; DOI {row['DOI']})"
            )
    return "\n".join(lines), result, plan
