from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from food_waste_agent.database import load_verified_records

out = ROOT / "data" / "verified_records.csv"
load_verified_records(ROOT).to_csv(out, index=False)
print("Exported", out)
