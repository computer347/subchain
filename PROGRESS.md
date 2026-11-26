# PROGRESS: subchain

**Tier:** Tool
**Phase:** 0 Spec
**Next step:** Mike confirms SPEC.md and answers open questions Q1–Q3 below; then Choice checkpoint sign-off and Phase 1 skeleton (small sample, placebo as the "method").

## How to run it
- Run: `uv run subchain all` (not built yet)
- Test: `uv run pytest -q` (not built yet)
- State check: `python3 tools/check_state.py`
- Try the core loop yourself: (Phase 1)

## Open questions (Phase 0)
- Q1: defense.gov contract announcements have no API — OK to scrape the daily HTML pages (polite, cached, once)? Fallback: USAspending action dates + 90-day lag (weaker timing).
- Q2: Price source — Stooq CSV (free, no key, delisted coverage unknown) vs yfinance (unofficial) vs EODHD/Polygon free tier (key, limits).
- Q3: SEC EDGAR needs a contact User-Agent — which email goes in `.env` (never committed)?

## Assumptions
- DoD awards appear in USAspending with ~90-day delay, so defense.gov is the event clock — assumed (check in Phase 1)
- FSRS `SubAwardReportYear/Month` = month the report became public — assumed (check: compare to report last-modified dates)
- Sub-award data usable from FY2015 — assumed
- Recipient UEIs often null in sub-awards, so name matching is required — checked (API sample 2026-11-26: UEI null on both rows)
- Short costs 50 bp + 5%/yr borrow — assumed
- Delisting return = last traded price — assumed (no CRSP)
- Python 3.12 via uv — asked (Mike, 2026-11-26)
- Scope FY2015–2025, both H1 and H2, Tool tier — asked (Mike, 2026-11-26)

## Core gate

### All tiers
- [ ] Every acceptance criterion has a passing check —
- [ ] Core loop works from a fresh start (fresh clone/install or cleared data) —
- [ ] No known bugs in the core loop —
- [ ] No failure on the core loop is silent —
- [ ] Stubs and fake data: none left in the core loop —
- [ ] No secrets in code or git history —
- [ ] Significant choices recorded; no risky assumption left unconfirmed —
- [ ] Explain-back done and the user understood it —
- [ ] User has done the core loop themselves and confirmed it —

### Tool and Product
- [ ] Automated tests derived from the spec cover every criterion and business-rule example —
- [ ] Combined edge cases listed and tested —
- [ ] Break-it pass done; every failure shows a visible error —
- [ ] Usability pass done: a newcomer could complete the core loop without being told how —
- [ ] Review checklist passed (`references/review-checklist.md`), including security and data safety —
- [ ] README setup works when followed literally from a fresh clone —
- [ ] `DEPENDENCIES.md` matches the code; no unlisted hardcoded paths —
- [ ] Core logic with calculations or rules: property tests, and a mutation check with no important surviving mutants —

### Study-specific (from research rules)
- [ ] Point-in-time assertion test passes (criterion 2) —
- [ ] Placebo and shuffled-link runs show no effect —
- [ ] Test set (FY2024–25) untouched until final run —

## Works (with evidence)
- USAspending sub-award search API reachable without key — POST /api/v2/search/spending_by_award/ (subawards=true) returned rows, 2026-11-26

## Unverified
- (none yet)

## Known bugs
- (none yet)

## Stubs / fakes
- (none yet)

## Overrides
- (none)

## Log (ten most recent; git has the rest)
- 2026-11-26: repo created, SPEC drafted, state files scaffolded (Phase 0)
