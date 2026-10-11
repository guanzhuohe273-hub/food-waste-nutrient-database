# Data provenance

The repository contains **408 manually checked literature-derived records** from **6 peer-reviewed original studies**, grouped into **211 experiment contexts** and **36 waste sources**. Original values, units, measurement bases, DOI and source locations are retained.

The schema deliberately distinguishes composition, extracted content, and recovery/yield semantics. Missing values remain missing, and published ranges are preserved textually instead of being replaced by invented midpoints.

The repository does **not** redistribute the source-paper PDFs. Bibliographic metadata and DOI links are provided so evidence can be traced back to the original publications.


For a compact Git history, the verified CSV is stored losslessly as a gzip/base64 payload in `data/records_part_*.b64`; `scripts/export_records.py` reconstructs the CSV.
