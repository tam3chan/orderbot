# DASHBOARD KNOWLEDGE BASE

**Generated:** 2026-04-24
**Parent:** `../AGENTS.md`

## OVERVIEW

Separate read-only Flask admin app for browsing food/non-food orders and templates; it shares `data/` directly and must not depend on bot startup.

## STRUCTURE

```
dashboard/
├── app.py                    # Flask factory, routes, static serving
├── auth.py                   # Dashboard token / insecure-local gate
├── config.py                 # Env-backed dashboard config
├── services/order_queries.py # Read-only Mongo query adapter
└── static/                   # Vanilla HTML/CSS/JS frontend
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/modify endpoint | `app.py` | Route handlers live inside `create_app()` |
| Auth behavior | `auth.py` | `Bearer` or `X-Dashboard-Token`; hmac compare |
| Env settings | `config.py` | `DASHBOARD_TOKEN`, `DASHBOARD_ALLOW_INSECURE` |
| Order/template reads | `services/order_queries.py` | Normalizes `food` / `nonfood`, clamps limit |
| Frontend behavior | `static/app.js` | Token login, API fetches, drawer rendering |
| Styling | `static/styles.css` | Plain CSS; no build step |
| API tests | `../tests/test_dashboard_api.py` | Fake DB via monkeypatch |

## CONVENTIONS

- Start with `python -m dashboard.app`, not `python bot.py`.
- Keep dashboard read-only: list/detail orders and templates only unless product scope explicitly changes.
- Query Mongo through `data.mongodb_repository.get_db()`; do not call Telegram bot handlers or `bot.py`.
- Validate request args before touching DB; invalid `type` or `limit` returns JSON 400.
- Keep list endpoints bounded with `normalize_limit(..., max_limit=100)`.
- Use token auth by default; `DASHBOARD_ALLOW_INSECURE=true` is local-only escape hatch when no token is configured.

## ANTI-PATTERNS

- Do not import `bot.py` or Telegram runtime from dashboard code.
- Do not add write/mutate routes casually; the current admin surface is read-only.
- Do not bypass `api_auth_required` on API routes unless adding an intentionally public asset/health behavior.
- Do not expose Mongo `_id` in dashboard JSON unless a caller contract explicitly needs it.
- Do not add a frontend build system unless the static app actually adopts one.

## GOTCHAS

- `/api/health` is auth-protected and returns 503 when `DASHBOARD_TOKEN` is missing unless insecure mode is enabled.
- `order_queries._collection()` maps `food` to `orders`/`templates` and `nonfood` to `nonfood_orders`/`nonfood_templates`.
- The dashboard package contains empty-looking subdirs plus `__pycache__`; do not infer implemented APIs from cache artifacts.
