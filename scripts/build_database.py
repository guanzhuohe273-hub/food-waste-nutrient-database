from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from food_waste_agent.database import build_from_project

path = build_from_project(ROOT)
print("Built", path)
