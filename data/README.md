# Data

The 408 verified evidence records are stored losslessly as gzip/base64 chunks (`records_part_*.b64`) to keep the Git history compact.

Run `python scripts/export_records.py` to materialize `data/verified_records.csv`. The SQLite builder derives paper and experiment tables from the verified records. Original source-paper PDFs are not redistributed.
