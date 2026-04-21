# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-21
**Commit:** ab351ce
**Branch:** (git fetch failed)

## OVERVIEW

Telegram bot (Python 3.11) for food ordering with FastAPI admin dashboard. Monorepo with 2 apps sharing MongoDB + R2 storage.

## STRUCTURE

```
order_bot/
├── bot.py              # Entry: python-telegram-bot ConversationHandler (12 states)
├── states.py           # OrderStates enum
├── db.py / r2.py      # DEPRECATED shims → use data/
├── requirements.txt     # Shared deps (bot + dashboard)
├── Dockerfile           # Runs: python bot.py (NOT dashboard)
├── handlers/           # Telegram command + conversation handlers
├── services/           # Business logic (Excel, Order)
├── models/             # Data models
├── data/               # MongoDB repository + R2 storage
├── keyboards/          # Telegram inline keyboard builders
├── dashboard/          # FastAPI app (separate entry point)
└── tests/              # pytest (minimal)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Bot entry point | `bot.py` | `main()` + ConversationHandler wiring |
| Conversation flow | `handlers/conversation/` | 6 sub-handlers for order FSM |
| Excel processing | `services/excel_service.py` | Parse + generate .xlsx |
| DB operations | `data/mongodb_repository.py` | Singleton MongoClient |
| R2 storage | `data/r2_storage.py` | boto3 S3 client |
| Dashboard API | `dashboard/main.py` | FastAPI app |
| Dashboard routes | `dashboard/api/` | auth, orders, analytics, excel, users |

## CONVENTIONS (THIS PROJECT)

- **snake_case** for functions/variables, **PascalCase** for classes
- **async/await** for Telegram handlers (python-telegram-bot v21+)
- **Singleton pattern** for MongoDB client (`get_client()`)
- **Module-level logger**: `logger = logging.getLogger(__name__)`
- **Type hints** throughout
- **DEPRECATED shims**: `db.py` → `data.mongodb_repository`, `r2.py` → `data.r2_storage`

## ANTI-PATTERNS (THIS PROJECT)

- **Never commit tokens**: All credentials via env vars only
- **Don't use `chore`/`docs` in `.claude` commits**: Per CLAUDE.md
- **No `chore`/`docs` in git commit messages for `.claude` directory**
- **Avoid circular imports**: `handlers/conversation/confirm.py` imports inside function to workaround

## UNIQUE STYLES

- **Vietnamese comments** in handlers and services
- **12-state ConversationHandler** for complex order flow
- **Dual-app repo**: Telegram bot + FastAPI dashboard in same repo
- **Dockerfile only runs bot**: Dashboard NOT containerized
- **GSD workflow artifacts** in `plans/` and `docs/` directories

## COMMANDS

```bash
# Bot
python bot.py

# Dashboard
cd dashboard && uvicorn dashboard.main:app --host 0.0.0.0 --port 8000

# Tests
pytest tests/

# Docker
docker build -t order-bot . && docker run order-bot
```

## NOTES

- **No formal linting**: No pyproject.toml, ruff.toml, or black config
- **pytest missing from requirements.txt** but imported in tests/test_bot.py
- **Deprecated modules still exist**: `db.py`, `r2.py` (backward compat shims)
- **CLAUDE.md is mandatory read** before planning/implementation
