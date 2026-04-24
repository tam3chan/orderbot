# DATA LAYER KNOWLEDGE BASE

**Generated:** 2026-04-24
**Parent:** `../AGENTS.md`

## OVERVIEW

MongoDB and R2 storage boundary. This directory replaces deprecated root shims and owns persistence contracts shared by bot and dashboard.

## STRUCTURE

```
data/
├── mongodb_repository.py # Mongo singleton, food/non-food orders/templates
├── r2_storage.py         # Cloudflare R2 workbook download into BytesIO
└── __init__.py           # Re-export boundary for current data APIs
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Food order persistence | `mongodb_repository.py` | `orders` collection keyed by ISO date |
| Food template persistence | `mongodb_repository.py` | `templates` collection keyed by `_id`/name |
| Non-food order persistence | `mongodb_repository.py` | `nonfood_orders`, separate from food |
| Non-food template persistence | `mongodb_repository.py` | `nonfood_templates`, separate from food |
| Test DB injection | `mongodb_repository.py` | `set_client()` swaps singleton client |
| R2 workbook download | `r2_storage.py` | Uses boto3 S3 client with R2 endpoint |
| Public imports | `__init__.py` | Keep exports in sync with repository functions |

## COLLECTION CONTRACTS

- Food orders: `orders`, date field is `YYYY-MM-DD`, unique date index created lazily.
- Food templates: `templates`, key is `_id == name`.
- Non-food orders: `nonfood_orders`, same date contract, isolated from food.
- Non-food templates: `nonfood_templates`, key is `_id == name`, isolated from food.
- `updated_at` is stored as `datetime.utcnow().isoformat()` string.

## CONVENTIONS

- New code imports from `data.mongodb_repository` / `data.r2_storage` or `data` re-exports, never root `db.py` / `r2.py`.
- Keep food and non-food APIs parallel but explicit; do not add a generic dynamic API if it hides collection separation.
- Tests should use `set_client()` or monkeypatch collection helpers; never hit live MongoDB.
- R2 download returns a seeked `io.BytesIO`; startup/bootstrap code owns fallback to local files.
- Missing `MONGODB_URI` is a hard runtime error; dashboard health catches ping failures as `False`.

## ANTI-PATTERNS

- Do not merge food and non-food collections.
- Do not create a fresh `MongoClient` per request; use the module singleton.
- Do not put Telegram or Flask request logic in this directory.
- Do not read `.env` here; environment is already process-level.
- Do not swallow R2 credential errors inside `r2_storage.py`; fallback decisions belong to startup code.

## TEST REFERENCES

- `../tests/test_nonfood_repository.py`: fake Mongo collection/cursor patterns.
- `../tests/test_dashboard_api.py`: dashboard monkeypatches `data.mongodb_repository.get_client`/DB behavior.
- `../tests/test_nonfood_bootstrap.py`: R2/local fallback contract lives at bot bootstrap, not in storage.
