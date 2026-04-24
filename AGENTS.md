# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-24
**Commit:** 55f4b37
**Branch:** master

Compact repo guidance for future OpenCode sessions. Keep this file high-signal; omit generic Python advice.

## OVERVIEW

Telegram order bot for food + non-food Excel ordering, with MongoDB persistence, Cloudflare R2 workbook loading, and a separate read-only Flask dashboard.

## SOURCE OF TRUTH

- Active production bot starts at `bot.py`; `Dockerfile` still runs only `python bot.py`.
- Dashboard is a separate Flask app started with `python -m dashboard.app`; never import or launch it through `bot.py`.
- README is partly stale: it still says 12 states and old `db.py`/`r2.py` ownership. Trust code + AGENTS files over README for architecture.
- `states.py` defines the shared 25-state FSM for food + non-food flows.
- `db.py` and `r2.py` are deprecated compatibility shims; new code uses `data/mongodb_repository.py` and `data/r2_storage.py`.

## STRUCTURE

```
order_bot/
├── bot.py                     # Telegram bootstrap, command registration, polling
├── states.py                  # 25 shared FSM states
├── handlers/                  # /start, /list, /tim, /cancel, conversation handlers
│   └── conversation/          # Mirrored food/non-food FSM; local AGENTS owns rules
├── keyboards/                 # Inline keyboard builders and callback payloads
├── services/                  # Excel parsing/generation and order orchestration
├── data/                      # MongoDB singleton repository and R2 storage boundary
├── dashboard/                 # Separate read-only Flask admin app + static frontend
├── models/                    # Small dataclasses; no Pydantic
└── tests/                     # Pytest suite with fake Telegram/Mongo/R2 seams
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Bot startup / handler wiring | `bot.py` | Env loading, Excel bootstrap, ConversationHandler setup |
| Shared state ids | `states.py` | Do not hardcode old 12-state assumptions |
| Food/non-food FSM changes | `handlers/conversation/` | Read local AGENTS first |
| Callback payload builders | `keyboards/` | Food inline keyboard helpers; callback prefixes matter |
| Excel catalog/order files | `services/excel_service.py` | Food + non-food workbook parsing/generation |
| Order orchestration wrapper | `services/order_service.py` | Thin food service facade |
| Mongo persistence | `data/mongodb_repository.py` | Food and non-food collections stay isolated |
| R2 workbook download | `data/r2_storage.py` | Startup-only download into memory |
| Dashboard API/UI | `dashboard/` | Separate Flask runtime; read-only admin surface |
| Tests/stubs | `tests/` | Read local AGENTS first |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `main()` | function | `bot.py` | Builds Telegram app, wires commands/conversations, starts polling |
| `_bootstrap_nonfood_assets()` | function | `bot.py` | Loads non-food workbook from R2 or local fallback |
| `OrderStates` | enum | `states.py` | Shared food + non-food ConversationHandler states |
| `ExcelService` | class | `services/excel_service.py` | Loads catalogs and writes order workbooks |
| `ExcelConfig` | class | `services/excel_service.py` | Food/non-food sheet and cell mapping constants |
| `get_client()` / `set_client()` | functions | `data/mongodb_repository.py` | Mongo singleton and test injection seam |
| `save_nonfood_order()` | function | `data/mongodb_repository.py` | Non-food order persistence contract |
| `download_excel()` | function | `data/r2_storage.py` | R2-to-BytesIO workbook loader |
| `create_app()` | function | `dashboard/app.py` | Flask dashboard factory |

## COMMANDS

```bash
pip install -r requirements.txt
python bot.py
python -m dashboard.app
pytest tests/
docker build -t order-bot . && docker run order-bot
```

- `pytest` is used by the repo but is not listed in `requirements.txt`; install it separately if needed.
- No ruff/black/mypy/pyproject/pytest config found; do not invent lint/typecheck commands.
- No GitHub Actions, Makefile, tox, or coverage config found.

## ENVIRONMENT AND SECRETS

- Required for real bot run: `BOT_TOKEN`, `MONGODB_URI`.
- Required for dashboard API auth: `DASHBOARD_TOKEN`; local-only insecure mode is `DASHBOARD_ALLOW_INSECURE=true`.
- Optional/common: `ALLOWED_USER_IDS`, `R2_ENDPOINT`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_OBJECT_KEY`, `EXCEL_PATH`, non-food workbook envs used in code/tests.
- Never read or commit `.env`; use `.env.example` only as a placeholder template, not trusted values.
- Preserve R2-backed Excel loading with local workbook fallback when changing startup/bootstrap code.

## PROJECT CONVENTIONS

- Preserve Vietnamese user-facing wording unless the task explicitly changes copy.
- Food and non-food flows are mirrored but separate: callback prefixes, session keys, collections, and templates must not collide.
- Nested ConversationHandlers are intentional for category, history, template, date, and non-food subflows.
- Some late imports in conversation handlers are intentional circular-import workarounds; inspect dependency direction before “cleaning them up”.
- Tests use fake Telegram modules/stubs, `monkeypatch`, and `asyncio.run(...)`; they must not need real Telegram, MongoDB, or R2.

## ANTI-PATTERNS

- Do not rely on stale README architecture claims when code/AGENTS disagree.
- Do not use `db.py` or `r2.py` in new code.
- Do not import `bot.py` from dashboard code.
- Do not blur food vs non-food callback prefixes, session keys, Mongo collections, or template APIs.
- Do not remove deferred imports in FSM handlers without proving circular dependencies stay safe.
- Do not add live external-service requirements to tests.
- Do not stage or rewrite unrelated working-tree changes unless explicitly asked.

## LOCAL KNOWLEDGE FILES

- `handlers/conversation/AGENTS.md`: FSM state, callback namespace, late-import rules.
- `tests/AGENTS.md`: fake Telegram runtime, monkeypatch seams, regression hotspots.
- `dashboard/AGENTS.md`: read-only Flask admin boundary.
- `data/AGENTS.md`: Mongo/R2 storage contracts and legacy shim avoidance.
- `services/AGENTS.md`: Excel workbook and service-layer ownership.
- `keyboards/AGENTS.md`: inline keyboard callback payload ownership.

## NOTES

- `tests/test_nonfood_conversation.py` is the large FSM regression hotspot.
- `tests/test_bot.py` is legacy/stale and expects old exports such as `fmt_qty` / `get_categories`; verify before relying on it as current behavior.
- `.planning/`, `.claude/`, and `CLAUDE.md` are gitignored in normal status output; force-add planning docs only when workflow explicitly requires committing them.
