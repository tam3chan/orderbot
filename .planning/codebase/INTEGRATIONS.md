# External Integrations

**Analysis Date:** 2026-04-24

## APIs & External Services

**Telegram Bot API:**
- Telegram is the primary user-facing integration.
  - SDK/Client: `python-telegram-bot>=21.0` from `requirements.txt`.
  - Entry point: `bot.py` builds `Application.builder().token(TOKEN).post_init(post_init).build()`.
  - Auth: `BOT_TOKEN` environment variable.
  - Network boundary: long-polling via `app.run_polling(drop_pending_updates=True)` in `bot.py`; no webhook server detected.
  - Commands registered in `bot.py`: `/order`, `/list`, `/tim`, `/cancel`, and conditional `/order_nonfood` when non-food assets load.
  - Access control: optional `ALLOWED_USER_IDS` comma-separated whitelist enforced by `authorized_only()` in `bot.py` when handlers use the wrapper.

**MongoDB:**
- MongoDB stores persisted food and non-food orders/templates.
  - SDK/Client: `pymongo[srv]==4.7.3`.
  - Implementation: `data/mongodb_repository.py`.
  - Auth/connection: `MONGODB_URI` environment variable.
  - Database name: `orderbot` in `data/mongodb_repository.py`.
  - Collections: `orders`, `templates`, `nonfood_orders`, `nonfood_templates`.
  - Indexes: unique `date` index created lazily for `orders` and `nonfood_orders`.
  - Client lifecycle: singleton `MongoClient` via `get_client()`; tests can inject a client through `set_client()`.

**Cloudflare R2 / S3-compatible object storage:**
- R2 stores Excel workbook templates for runtime download.
  - SDK/Client: `boto3==1.34.69` with `botocore.config.Config(signature_version="s3v4")`.
  - Implementation: `data/r2_storage.py`.
  - Auth: `R2_ENDPOINT`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`.
  - Bucket: `R2_BUCKET`, default `orderbot`.
  - Food object key: `R2_OBJECT_KEY`, default `DAILY_ORDER_MIN_xlsx.xlsx`.
  - Non-food object key: `NONFOOD_R2_OBJECT_KEY` consumed by `_bootstrap_nonfood_assets()` in `bot.py`.
  - Network boundary: `download_fileobj()` downloads into an in-memory `io.BytesIO`; no uploads detected.

**Excel workbook processing:**
- Excel templates are a business-system boundary, not a remote API.
  - Library: `openpyxl==3.1.2`.
  - Implementation: `services/excel_service.py`.
  - Food input sheet: `Food T01`.
  - Food output sheet: `PR NOODLE`.
  - Non-food input sheets: `CCDC` and `VTTH`.
  - Non-food output sheet: `PR NOODLE`.
  - Output format: generated `.xlsx` files returned as `io.BytesIO` from `build_order_excel()` and `build_order_excel_nonfood()`.

## Data Storage

**Databases:**
- MongoDB / MongoDB Atlas-compatible service.
  - Connection: `MONGODB_URI`.
  - Client: `pymongo.MongoClient` in `data/mongodb_repository.py`.
  - DB name: `orderbot`.
  - Food persistence: `save_order()`, `get_order()`, `get_recent_dates()`, `get_order_by_iso()`, `save_template()`, `get_template()`, `list_templates()`.
  - Non-food persistence: `save_nonfood_order()`, `get_nonfood_order()`, `get_recent_nonfood_dates()`, `get_nonfood_order_by_iso()`, `save_nonfood_template()`, `get_nonfood_template()`, `list_nonfood_templates()`.

**File/Object Storage:**
- Cloudflare R2 via S3-compatible boto3 client in `data/r2_storage.py`.
- Local filesystem fallback for workbook templates through `EXCEL_PATH` and `NONFOOD_EXCEL_PATH` in `bot.py`.
- `*.xlsx` files are ignored by `.gitignore`; local templates must be supplied outside committed source.

**Caching:**
- In-memory workbook buffers: `EXCEL_BUFFER` in `bot.py` stores food workbook downloaded from R2.
- `ExcelService` caches parsed food items/categories in `_items` and `_categories` after `load_items()`.
- Non-food loaded items/categories are stored in `app.bot_data` by `_build_bot_data()` in `bot.py`.
- No Redis, Memcached, or external cache detected.

## Authentication & Identity

**Telegram identity:**
- User identity comes from `update.effective_user.id` in `bot.py`.
- Whitelist is configured with `ALLOWED_USER_IDS`; empty/missing whitelist permits all users for handlers that use `authorized_only()`.

**Service credentials:**
- Telegram token: `BOT_TOKEN`.
- MongoDB URI: `MONGODB_URI`.
- R2 credentials: `R2_ACCESS_KEY` and `R2_SECRET_KEY` with endpoint `R2_ENDPOINT`.
- Secrets are environment variables loaded by `python-dotenv`; `.env` is ignored by `.gitignore` and must not be committed.

## Monitoring & Observability

**Error Tracking:**
- No external error tracking service detected.

**Logs:**
- Standard Python logging configured in `bot.py` with format `%(asctime)s - %(levelname)s - %(message)s` at `INFO` level.
- R2 download progress is logged in `data/r2_storage.py` without credential values.
- Non-food bootstrap failures are logged in `bot.py`; failures disable non-food flow rather than terminating food startup.
- Excel formula translation errors are logged in `services/excel_service.py`.

## CI/CD & Deployment

**Hosting:**
- `README.md` mentions Railway.
- `Dockerfile` is the concrete deployable runtime and starts only `python bot.py`.
- No active dashboard deployment artifact detected.

**CI Pipeline:**
- None detected in the repository snapshot; no `.github/workflows/` files appeared in codebase exploration.

## Environment Configuration

**Required env vars:**
- `BOT_TOKEN` - required at startup by `bot.py`.
- `MONGODB_URI` - required when `data/mongodb_repository.py` opens the database.

**Optional env vars:**
- `ALLOWED_USER_IDS` - comma-separated Telegram IDs for whitelist access.
- `EXCEL_PATH` - local food workbook path, default `DAILY_ORDER_MIN_xlsx.xlsx`.
- `R2_ENDPOINT` - Cloudflare R2 endpoint.
- `R2_ACCESS_KEY` - Cloudflare R2 access key.
- `R2_SECRET_KEY` - Cloudflare R2 secret key.
- `R2_BUCKET` - R2 bucket name, default `orderbot`.
- `R2_OBJECT_KEY` - food workbook object key, default `DAILY_ORDER_MIN_xlsx.xlsx`.
- `NONFOOD_R2_OBJECT_KEY` - non-food workbook object key for R2 bootstrap.
- `NONFOOD_EXCEL_PATH` - local non-food workbook path, default `ORDER NONFOOD MIN xlsx.xlsx`.

**Secrets location:**
- Local development: `.env` loaded by `load_dotenv()` in `bot.py`; `.env` is ignored and was not read.
- Production: platform environment variables (for example Railway dashboard as described in `README.md`).

## Local Fallback Behavior

**Food workbook:**
- `_init_excel_buffer()` in `bot.py` downloads from R2 only when `R2_ENDPOINT` and `R2_ACCESS_KEY` exist.
- When R2 is not configured, `bot.py` logs local fallback and `ExcelService(buffer=EXCEL_BUFFER, local_path=EXCEL_PATH)` loads from the local path.
- If R2 environment is partially configured, `data/r2_storage.py` may still require `R2_SECRET_KEY` at client creation because it indexes `os.environ["R2_SECRET_KEY"]`.

**Non-food workbook:**
- `_bootstrap_nonfood_assets()` in `bot.py` attempts R2 only when `R2_ENDPOINT`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, and `NONFOOD_R2_OBJECT_KEY` are present.
- If R2 download fails, non-food bootstrap falls back to local `NONFOOD_EXCEL_PATH` or `ORDER NONFOOD MIN xlsx.xlsx`.
- If local loading or item parsing fails, non-food flow is disabled while the food bot remains enabled.

## Webhooks & Callbacks

**Incoming:**
- Telegram updates arrive through long polling; no HTTP webhook endpoint is defined.
- Bot callback query patterns are configured in `bot.py` and nested conversation modules under `handlers/conversation/`.

**Outgoing:**
- Telegram API calls send messages, bot commands, callback responses, and Excel documents through `python-telegram-bot` handlers.
- MongoDB writes occur through `data/mongodb_repository.py` during order/template saves.
- R2 object downloads occur once at startup for configured workbooks through `data/r2_storage.py`.

## Deprecated Shims

**Database shim:**
- `db.py` is deprecated and re-exports `data.mongodb_repository` with a `DeprecationWarning`.
- New code should import from `data` or `data.mongodb_repository.py`.

**R2 shim:**
- `r2.py` is deprecated and re-exports `data.r2_storage` with a `DeprecationWarning`.
- New code should import from `data.r2_storage.py` or `data`.

---

*Integration audit: 2026-04-24*
