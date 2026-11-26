# DEPENDENCIES: subchain

Updated: 2026-11-26. Update in the same change as any structural edit.

## Module map
| File / module | Purpose | Depends on | Used by |
|---|---|---|---|
| src/subchain/config.py | all tunable values (planned) | — | everything |

## Data flow (core loop)
defense.gov announcements + USAspending sub-awards + prices → point-in-time links → events → CARs → results table

## Paths
| Path | Used in | In config? | Why hardcoded (if so) |
|---|---|---|---|
| data/ | all fetchers (planned) | yes (DATA_DIR) | — |

## Environment variables
| Name | Used in | Required? | Example |
|---|---|---|---|
| SEC_USER_AGENT | EDGAR fetcher (planned) | yes | "subchain research <email>" |

## External services & APIs
| Service | Used in | Auth | Failure behaviour shown to user |
|---|---|---|---|
| USAspending API v2 | fetch (planned) | none | raise with endpoint + status |
| SEC EDGAR | fetch (planned) | User-Agent | raise with endpoint + status |
| defense.gov contracts | fetch (planned, pending Q1) | none | raise |
| price source | fetch (pending Q2) | TBD | raise |

## Data stores
| DB / file / bucket | Tables / keys | Read by | Written by |
|---|---|---|---|
| data/raw/ | cached API responses | normalisers | fetchers |
| data/*.parquet | normalised tables | DuckDB queries | normalisers |
