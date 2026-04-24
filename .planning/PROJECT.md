# Project: Order Bot

Telegram ordering bot for Vietnamese food and non-food purchase workflows, producing Excel order files backed by MongoDB persistence and Cloudflare R2/local workbook templates.

## Current state

- Brownfield Python 3.11 repository.
- Active runtime is `bot.py`; Dockerfile runs only the Telegram bot.
- Main product flow is Telegram conversation-based ordering.
- Code supports mirrored food and non-food order flows.
- Dashboard directory exists but is scaffold-only, not a working app.
- `.planning/codebase/` exists but is currently empty because mapper agents were interrupted.

## Users

- Restaurant/store operators who create recurring supplier order files.
- Authorized Telegram users listed in `ALLOWED_USER_IDS`.
- Future admins who may need order search, exports, retry tools, and operational visibility.

## Core jobs

1. Create order files quickly from known supplier/catalog spreadsheets.
2. Reuse recent orders/templates to reduce repetitive input.
3. Keep food and non-food workflows isolated and reliable.
4. Generate Excel outputs that match supplier/workbook expectations.
5. Persist order history for lookup, templates, and future admin tooling.

## Active architecture

- `bot.py`: entrypoint, service bootstrap, ConversationHandler wiring, polling.
- `states.py`: 25 shared enum states across food/non-food FSMs.
- `handlers/`: commands and conversation handlers.
- `services/`: Excel and order service logic.
- `data/`: MongoDB and R2 boundaries.
- `models/`: dataclass domain models.
- `tests/`: pytest regression suite with custom Telegram stubs.

## Workflow preferences

- Mode: rigorous.
- Research: deep.
- Roadmap scope: stabilization, new features, dashboard revival.

## Open questions

- Which exact order workflow has highest production usage: food, non-food, or both equally?
- Who is the dashboard user, and what auth source should be trusted?
