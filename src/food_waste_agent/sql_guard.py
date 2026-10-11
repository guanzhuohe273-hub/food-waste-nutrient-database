from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "replace", "attach", "detach",
    "pragma", "vacuum", "reindex", "analyze", "begin", "commit", "rollback", "savepoint",
    "release", "load_extension"
}
ALLOWED_OBJECTS = {"verified_food_waste_records", "compatibility_records", "papers", "experiments"}

@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str


def validate_sql(sql: str) -> GuardResult:
    text = sql.strip()
    if not text:
        return GuardResult(False, "empty SQL")
    if ";" in text.rstrip(";"):
        return GuardResult(False, "multiple statements are not allowed")
    if not re.match(r"(?is)^\s*(select|with)\b", text):
        return GuardResult(False, "only SELECT/WITH statements are allowed")
    words = set(re.findall(r"[a-z_]+", text.casefold()))
    bad = sorted(words & FORBIDDEN)
    if bad:
        return GuardResult(False, f"forbidden keyword: {bad[0]}")

    ctes = set(re.findall(r"(?is)(?:with|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+as\s*\(", text))
    objects = set(re.findall(r"(?is)\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)", text))
    disallowed = sorted(obj for obj in objects if obj not in ALLOWED_OBJECTS and obj not in ctes)
    if disallowed:
        return GuardResult(False, f"object not allow-listed: {disallowed[0]}")
    return GuardResult(True, "ok")


def execute_guarded(db_path: str | Path, sql: str, max_rows: int = 100, max_steps: int = 100_000) -> list[dict]:
    decision = validate_sql(sql)
    if not decision.allowed:
        raise ValueError(decision.reason)

    path = Path(db_path).resolve()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    denied_actions = {
        sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
        sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_PRAGMA,
    }
    def authorizer(action, arg1, arg2, dbname, source):
        return sqlite3.SQLITE_DENY if action in denied_actions else sqlite3.SQLITE_OK
    conn.set_authorizer(authorizer)

    ticks = {"n": 0}
    def progress():
        ticks["n"] += 1000
        return 1 if ticks["n"] > max_steps else 0
    conn.set_progress_handler(progress, 1000)

    try:
        cur = conn.execute(sql)
        rows = [dict(r) for r in cur.fetchmany(max_rows + 1)]
        return rows[:max_rows]
    finally:
        conn.close()
