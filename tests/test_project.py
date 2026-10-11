from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from food_waste_agent.database import build_from_project, database_stats
from food_waste_agent.semantic import normalize_question
from food_waste_agent.sql_guard import validate_sql, execute_guarded
from food_waste_agent.agent import HybridEvidenceAgent


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "food_waste.db"
    build_from_project(ROOT, path)
    return path


def _ids(result):
    return {row["Record_ID"] for row in result["rows"] if row.get("Record_ID")}


def test_database_scale(db_path):
    assert database_stats(db_path) == {
        "records": 408,
        "papers": 6,
        "experiments": 211,
        "waste_sources": 36,
        "targets": 19,
    }


@pytest.mark.parametrize("sql", [
    "DROP TABLE papers",
    "DELETE FROM papers",
    "PRAGMA table_info(papers)",
    "SELECT * FROM sqlite_master",
    "SELECT 1; SELECT 2;",
])
def test_guard_rejects_unsafe_sql(sql):
    assert not validate_sql(sql).allowed


def test_guard_allows_verified_view(db_path):
    sql = "SELECT Record_ID FROM verified_food_waste_records LIMIT 2"
    assert validate_sql(sql).allowed
    assert len(execute_guarded(db_path, sql)) == 2


def test_semantic_normalization():
    assert "peel" in normalize_question("clementine rind pectin").fractions
    assert "total dietary fibre" in normalize_question("highest total dietary fiber").targets
    assert normalize_question("recovery of protein from BSG").targets == ("protein recovery",)


def test_pectin_ranking(db_path):
    result = HybridEvidenceAgent(db_path).ask(
        "Which clementine rind conditions produced the highest pectin yield?"
    )
    assert "FWN0385" in _ids(result)


def test_protein_recovery(db_path):
    result = HybridEvidenceAgent(db_path).ask(
        "Best recovery of protein from spent grain?"
    )
    assert "FWN0404" in _ids(result)


def test_chinese_count_query(db_path):
    result = HybridEvidenceAgent(db_path).ask("香蕉皮有多少条钙数据？")
    assert result["rows"][0]["record_count"] == 2
