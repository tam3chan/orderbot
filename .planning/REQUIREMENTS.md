# Requirements

## Scope

Initialize the roadmap for a brownfield Telegram ordering bot. The roadmap covers stabilization of the existing bot, user-facing feature expansion, and revival of the inactive dashboard scaffold.

## Goals

1. Make existing food and non-food ordering flows reliable and restart-safe.
2. Align docs, tests, dependencies, and environment configuration with current code.
3. Preserve Excel workflow compatibility while improving validation and storage safety.
4. Improve operator UX for long Telegram order flows.
5. Add operational visibility and prepare a minimal admin dashboard/API.

## Functional requirements

- Continue supporting `/start`, `/order`, `/list`, `/tim`, and `/cancel`.
- Keep food and non-food state/session/callback namespaces isolated.
- Preserve recent orders, templates, date/history search, and Excel generation.
- Keep local Excel fallback working when R2 is unavailable.
- Validate required config and workbook schema with actionable errors.
- Guard final confirmation against duplicate submissions.
- Add central logging/error handling for unhandled exceptions.
- Support clearer cancel/back/edit/resume behavior in long flows.
- Revive dashboard only behind authenticated admin access.

## Quality requirements

- Pytest suite must pass before phase completion.
- Add targeted regression tests for each fixed bug or workflow behavior change.
- Preserve async handler style and existing test seams.
- No production credentials in commits.

## Acceptance criteria

- Planning docs exist and describe current product accurately.
- Roadmap has phases for stabilization, feature growth, and dashboard revival.
- Next command is actionable: `/gsd-plan-phase 1`.

## Open questions

- Which exact order workflow has highest production usage: food, non-food, or both equally?
- Who is the dashboard user, and what auth source should be trusted?
