from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "food_waste.db"

@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("FOOD_WASTE_DB", str(DEFAULT_DB)))
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    max_rows: int = int(os.getenv("FOOD_WASTE_MAX_ROWS", "100"))
    max_steps: int = int(os.getenv("FOOD_WASTE_MAX_STEPS", "100000"))

settings = Settings()
