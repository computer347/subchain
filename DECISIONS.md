# DECISIONS: subchain

One entry per significant choice. Newest first.

## D-002: Storage = Parquet files queried with DuckDB (2026-11-26)
- **Choice:** raw API pulls cached as JSON → normalised Parquet in `data/`; DuckDB for joins (point-in-time link building).
- **Default I almost used:** pandas + CSV.
- **Options considered:** A — CSV + pandas (simple; slow and memory-heavy at millions of sub-award rows, loses dtypes) / B — Parquet + DuckDB (fast columnar joins, single file, no server) / C — Postgres (overkill, needs a server).
- **Constraints that decided it:** millions of sub-award rows, single user on a laptop, rerun < 30 min.
- **Assumptions:** sub-award volume fits on local disk (< 10 GB) — safe.
- **Why:** B handles as-of joins on millions of rows on a laptop with no service to run.
- **Reversal trigger:** data > 50 GB or need for concurrent writers.
- **Status:** active

## D-001: Stack = Python 3.12, uv, pandas for stats (2026-11-26)
- **Choice:** Python 3.12, uv-managed with `uv.lock`; pandas/numpy/scipy for event study; httpx for API calls; pytest.
- **Default I almost used:** same — Mike's chosen environment.
- **Options considered:** A — uv (lockfile, reproducible) / B — venv+pip / C — conda.
- **Constraints that decided it:** reproducible from fresh clone (criterion 1); Mike asked for uv.
- **Assumptions:** uv available on Mike's Mac — known (uv present in session VM; confirm on Mac).
- **Why:** Mike's choice; lockfile satisfies reproducibility.
- **Reversal trigger:** none expected.
- **Status:** active
