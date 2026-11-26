# subchain

Every new session: use the builder skill, read SPEC.md and PROGRESS.md first, run `python3 tools/check_state.py`.

- Run: `uv run subchain all`
- Test: `uv run pytest -q`
- Config: `src/subchain/config.py`; secrets in `.env` (git-ignored)
- Test set (events FY2024–FY2025) must not be evaluated until the final run.
