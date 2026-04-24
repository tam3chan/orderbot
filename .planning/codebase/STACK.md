# Technology Stack

**Analysis Date:** 2026-04-24

## Languages

**Primary:**
- Python 3.11 - active Telegram bot runtime, pinned by `Dockerfile` line 1 (`FROM python:3.11-slim`) and described in `README.md`.

**Secondary:**
- Markdown - project and workflow documentation in `README.md`, `AGENTS.md`, `CLAUDE.md`, and `.planning/`.
- Excel workbooks (`*.xlsx`) - business templates and generated order artifacts consumed by `services/excel_service.py`.

## Runtime

**Environment:**
- CPython 3.11 in production/container via `Dockerfile`.
- Local development can run directly with `python bot.py` from repository root.
- `python-dotenv` loads `.env` automatically from `bot.py`; never read or commit `.env` contents.

**Package Manager:**
- pip with `requirements.txt`.
- Lockfile: missing. Dependencies are partially pinned (`openpyxl`, `python-dotenv`, `pymongo[srv]`, `boto3`) and partially ranged (`python-telegram-bot>=21.0`).

## Frameworks

**Core:**
- `python-telegram-bot>=21.0` - Telegram bot framework used by `bot.py` with `Application`, `CommandHandler`, `CallbackQueryHandler`, `MessageHandler`, `filters`, and `ConversationHandler`.
- `pymongo[srv]==4.7.3` - MongoDB client used by `data/mongodb_repository.py` for orders and templates.
- `boto3==1.34.69` - S3-compatible client used by `data/r2_storage.py` for Cloudflare R2 workbook downloads.
- `openpyxl==3.1.2` - Excel parser/generator used by `services/excel_service.py`.
- `python-dotenv==1.0.1` - environment loading used by `bot.py`.

**Testing:**
- pytest is used by files in `tests/` (`tests/test_bot.py`, `tests/test_nonfood_conversation.py`, `tests/test_nonfood_excel_service.py`, `tests/test_nonfood_repository.py`, `tests/test_food_flow_regression.py`).
- pytest is not listed in `requirements.txt`; install it separately for local test runs.
- No pytest config file detected (`pytest.ini`, `pyproject.toml`, `setup.cfg`, or `tox.ini` absent).

**Build/Dev:**
- Docker is the only detected build/deployment packaging layer (`Dockerfile`).
- No formal lint/format/type-check config detected (`pyproject.toml`, `ruff.toml`, `.flake8`, `mypy.ini`, `.prettierrc`, `eslint.config.*` absent).

## Key Dependencies

**Critical:**
- `python-telegram-bot>=21.0` - all active bot handlers in `bot.py` and `handlers/` depend on async PTB v21 APIs.
- `pymongo[srv]==4.7.3` - required for `data/mongodb_repository.py`; `MONGODB_URI` must be configured before DB-backed commands work.
- `openpyxl==3.1.2` - required for item catalog loading and Excel output generation in `services/excel_service.py`.
- `boto3==1.34.69` - required only when Cloudflare R2 variables are configured; otherwise workbook loading falls back to local Excel files.

**Infrastructure:**
- `python-dotenv==1.0.1` - allows local `.env` development without changing production env var handling.
- `botocore.config.Config` - imported inside `data/r2_storage.py` through boto3/botocore for S3 signature version `s3v4`.

## Configuration

**Environment:**
- `bot.py` requires `BOT_TOKEN`; startup exits with status 1 if missing.
- `MONGODB_URI` is required by `data/mongodb_repository.py` when DB access occurs; missing value raises `RuntimeError`.
- `ALLOWED_USER_IDS` is optional; when present, `bot.py` parses comma-separated Telegram user IDs and rejects unauthorized users.
- Food workbook path defaults to `DAILY_ORDER_MIN_xlsx.xlsx` through `EXCEL_PATH` in `bot.py`.
- Non-food workbook path defaults to `ORDER NONFOOD MIN xlsx.xlsx`; `NONFOOD_EXCEL_PATH` can override local path.
- R2 is enabled when `R2_ENDPOINT` and `R2_ACCESS_KEY` are present for food startup; non-food R2 additionally requires `R2_SECRET_KEY` and `NONFOOD_R2_OBJECT_KEY`.

**Build:**
- `requirements.txt` is the dependency manifest.
- `Dockerfile` installs dependencies with `pip install --no-cache-dir -r requirements.txt`, copies the full repo, and runs `python bot.py`.
- `.gitignore` excludes `.env`, `*.xlsx`, `.planning`, `.claude`, `docs`, and cache artifacts.

## Commands

**Local runtime:**
```bash
pip install -r requirements.txt
python bot.py
```

**Tests:**
```bash
pytest tests/
```

**Docker:**
```bash
docker build -t order-bot .
docker run --env-file .env order-bot
```

## Active vs Inactive Code

**Active runtime:**
- `bot.py` is the production entry point and wires all command/conversation handlers.
- `handlers/` contains active Telegram command and conversation modules.
- `services/excel_service.py` handles workbook parsing and generated order files.
- `services/order_service.py` orchestrates DB persistence plus Excel generation.
- `data/mongodb_repository.py` is the active MongoDB repository.
- `data/r2_storage.py` is the active Cloudflare R2/S3 storage client.
- `models/`, `keyboards/`, and `states.py` support the active bot.

**Inactive or compatibility-only:**
- `dashboard/` contains only scaffolding/cache artifacts in the current checkout; do not treat it as deployable application code.
- `db.py` is a deprecated shim that re-exports `data.mongodb_repository`.
- `r2.py` is a deprecated shim that re-exports `data.r2_storage`.
- `README.md` contains stale structure details (for example older 12-state wording and direct `db.py`/`r2.py` references); prefer current source files for implementation decisions.

## Platform Requirements

**Development:**
- Python 3.11-compatible environment.
- Network access to Telegram API for live bot usage.
- MongoDB access via `MONGODB_URI` for order/template persistence.
- Local workbook files if R2 is not configured: `DAILY_ORDER_MIN_xlsx.xlsx` for food flow and `ORDER NONFOOD MIN xlsx.xlsx` for non-food flow unless env overrides are set.

**Production:**
- Container or host that runs `python bot.py` as a long-lived polling process.
- Telegram bot token from BotFather in `BOT_TOKEN`.
- MongoDB Atlas or compatible MongoDB reachable from the runtime.
- Optional Cloudflare R2 bucket for workbook templates.
- `README.md` mentions Railway deployment; `Dockerfile` is the concrete deployment artifact in this repo.

---

*Stack analysis: 2026-04-24*
