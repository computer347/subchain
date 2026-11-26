# SPEC: subchain

**Tier:** Tool — research Mike relies on for months and will show employers; not used by others, no money at stake.
**Question:** When a US defence prime contractor wins a contract, do its *listed suppliers* (identified from public sub-award data) earn abnormal returns afterwards — and do listed incumbents that *lose* a recompete underperform?
**Deadline:** none

Anything marked "(assumed)" is a guess not yet confirmed by Mike.

## Hypotheses
- **H1 — supplier spillover (long leg).** After a DoD award announcement to prime P, listed suppliers S linked to P (via sub-awards published *before* the event) show positive abnormal return over trading days [+1, +20], growing with the implied pass-through shock. Contradicted if CAR ≤ 0 or indistinguishable from placebo.
- **H2 — recompete loser (short leg).** When work previously held by listed incumbent I is re-awarded to a different firm, I shows negative abnormal return over [+1, +60]. Contradicted if CAR ≥ 0 or indistinguishable from placebo. Exact recompete-matching rule finalised in Phase 1 after inspecting real records (assumed), and frozen before any H2 returns are looked at.

## Data (public only — no WRDS)
- **Prime award events:** DoD daily contract announcements (defense.gov/News/Contracts, ≥ $7.5M, ~5pm ET). Needed because FPDS/USAspending publishes DoD awards with a ~90-day delay, so USAspending dates are not tradeable timestamps (assumed; verified in Phase 1).
- **Supplier links + incumbents:** USAspending API v2 (prime contracts + FSRS sub-awards), no key.
- **Company → ticker:** SEC EDGAR `company_tickers.json` + full-text search; parent mapping where the sub-awardee is a subsidiary.
- **Prices + market caps:** source TBD (Q2 below). Benchmarks: ITA (US aerospace & defence ETF), IWM (small caps).
- **Period:** award events Oct 2014 – Sep 2025 (FY2015–FY2025); prices to Dec 2025 so the last events get full 60-day windows.
- **Split (by event date):** explore FY2015–FY2021 / validation FY2022–FY2023 / **test FY2024–FY2025 — not looked at until the end.**
- **Point-in-time rules:**
  - A sub-award is usable from the 1st day of the month after its FSRS *report* month (`SubAwardReportYear/Month`), never by its action date.
  - Supplier link weight uses sub-awards reported in the trailing 36 months before the event.
  - Market cap = price × shares outstanding from the most recent 10-Q/10-K filed *before* the event.
  - Delisted firms stay in the sample; delisting return taken from last traded price (assumed, no CRSP).

## Baseline
- Same supplier, random non-event dates (placebo): expected CAR ≈ 0.
- The prime P's own CAR on the same event (the "direct" effect; prior evidence says ≈ 0 after sector adjustment).
- Benchmark for abnormal return: ITA; robustness vs IWM.

## Metric and decision rule
- **Metric:** mean CAR (sum of daily returns minus ITA daily returns) over [+1, +20] (H1) and [+1, +60] (H2), entry at close of D+1 (D = announcement date, posted after close).
- **Costs:** 20 bp round trip long; short 50 bp round trip + 5%/yr borrow (assumed for small caps).
- **Support:** net-of-cost mean CAR > 0 (H1) / < 0 (H2) on validation, 95% bootstrap CI (clustered by event date) excluding 0, AND exceeds the placebo distribution's 95th percentile.
- **No effect:** CI includes 0 or within placebo range. **Opposite:** CI entirely on the wrong side.
- **Reported with:** n events, n distinct firms, CI, placebo percentile, all runs logged.

## Core loop
announcements + sub-awards + prices → point-in-time supplier links → events (shock = award × link weight ÷ supplier mcap ≥ 1%) → CARs vs ITA → table vs placebo & baseline

## Acceptance criteria (pipeline, not results)
1. `uv run subchain all` from a fresh clone (with the cached raw snapshot) reproduces the reported tables exactly.
2. Automated assertion: no event uses a sub-award whose report month is ≥ the event month, or a market cap from a filing after the event.
3. Placebo run (random dates, same firms) gives CI covering 0.
4. Shuffled-link run (events assigned to random listed suppliers) gives no effect.
5. Worked examples below pass as unit tests.
6. Manual audit of 50 random name→ticker matches: ≥ 95% correct, results recorded in PROGRESS.md.
7. Raw API pulls cached with retrieval timestamp; reruns don't refetch unless forced.
8. Every results run Mike or Claude looks at is appended to `RESULTS_LOG.md`.

## Worked examples
- **Link weight:** P published $1,000M of sub-awards in the trailing 36 months, $30M to S → w = 0.03.
- **Shock:** award to P = $500M → implied pass-through = 500 × 0.03 = $15M; S mcap = $300M → shock = 5.0% ≥ 1% → event. Same award, S mcap $3,000M → 0.5% → not an event.
- **Point-in-time:** sub-award reported in May 2021 → usable from 2021-06-01. Event on 2021-05-20 cannot use it; event on 2021-06-01 can.
- **CAR:** S returns +2.0%, −1.0%, +0.5%; ITA +1.0%, 0.0%, +0.5% → AR = +1.0, −1.0, 0.0 → CAR = 0.0%. Net long = 0.0% − 0.20% = −0.20%.
- **Timing:** announcement Tue 2023-03-07 (after close) → entry at close Wed 2023-03-08; [+1, +20] = the 20 trading days after that close.

## Constraints
- Sub-awards for DoD FY2015–2025: estimated millions of rows (unknown until pulled); announcements ~250/year × ~10 years.
- Runs on Mike's MacBook (Apple Silicon); full pipeline target < 30 min after raw data is cached.
- Public APIs only; polite rate limits; SEC requires a contact User-Agent.

## Out of scope (v1)
- Non-DoD agencies; Nordic/EU (TED, Hilma); SBIR/OTA early signals; revenue nowcasting; raw-material (commodity input) chain; intraday timing; "fade the gap" short on the prime itself; live trading.

## Stack & data sources
- Python 3.12 via uv (lockfile pinned); DuckDB over Parquet for storage; pandas for analysis (see DECISIONS.md).
- Config file: `src/subchain/config.py`; secrets/contact info in `.env` (git-ignored).
- Data/APIs: USAspending API v2, SEC EDGAR, defense.gov contract announcements, price source TBD (checked public-apis list: yes — SEC EDGAR listed; price candidates EODHD, Polygon, Alpha Vantage, FMP; no free API for DoD daily announcements).

## Variants (Phase 3, expectation written before running)
_(none yet)_

## Spec changes
Any change to hypothesis, metric, split, or inclusion rules after results were seen is marked "post hoc".
- 2026-11-26: spec drafted (not post hoc).
