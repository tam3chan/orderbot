# Roadmap

## Milestone 1: Stabilize and document current bot

### Phase 1: Refresh codebase map and developer docs

- Generate `.planning/codebase/` documents.
- Update README stale 12-state/module wording.
- Document active food/non-food flows and dashboard scaffold status.
- Align `.env.example` with actual supported env vars.

### Phase 2: Test and dependency baseline

- Add/clarify pytest dependency strategy.
- Review stale `tests/test_bot.py` and update or retire broken assumptions.
- Add baseline command notes for running tests.
- Verify `pytest tests/` passes.

### Phase 3: Startup/config hardening

- Centralize env var validation.
- Improve startup logs/errors for Telegram token, MongoDB URI, Excel/R2 config.
- Document local fallback behavior.
- Add bootstrap fallback tests where feasible.

## Milestone 2: Reliability and data integrity

### Phase 4: MongoDB repository reliability

- Review singleton MongoClient settings.
- Add explicit timeout policy.
- Define needed indexes for orders/templates/history.
- Document collection boundaries for food and non-food data.

### Phase 5: Idempotent order finalization

- Add idempotency/session guard around final confirmation.
- Store clear order/export IDs.
- Add regression tests for duplicate callback/finalize behavior.

### Phase 6: Central error handling and observability baseline

- Central Telegram error handler.
- Structured log fields for chat/user/order/export IDs.
- Optional admin alert path for critical failures.

## Milestone 3: Excel and storage hardening

### Phase 7: Workbook schema validation

- Explicit sheet/column validation for food and non-food workbooks.
- User/admin-facing error messages for invalid templates.
- Regression tests for missing sheet/column cases.

### Phase 8: R2/S3 export safety

- Review upload/download helpers.
- Define deterministic object key convention.
- Store export metadata where needed.
- Consider presigned URL path for admin/download flows.

## Milestone 4: Operator UX improvements

### Phase 9: Draft resume and navigation polish

- Add or improve back/edit/cancel behavior for key steps.
- Add draft resume semantics where feasible.
- Make error messages actionable and Vietnamese-friendly.

### Phase 10: Faster repeat ordering

- Improve recent order/template discovery.
- Add shortcuts for common quantities/items if validated by users.
- Add clearer confirmation summaries.

## Milestone 5: Dashboard revival

### Phase 11: Dashboard architecture decision

- Decide FastAPI vs other approach.
- Define dashboard auth model.
- Define read-only operational views.
- Replace or clean inactive skeleton files.

### Phase 12: Minimal authenticated admin dashboard/API

- Authenticated admin entrypoint.
- Order search/filter view or API.
- Export lookup/status view.
- Health/status endpoint.

### Phase 13: Admin support actions

- Retry export/send action.
- Manual status update where needed.
- Audit log for admin actions.

## Backlog

- CI pipeline for tests.
- Deployment/staging environment split.
- Metrics dashboard and alert thresholds.
- Data retention/cleanup policy for generated files.
- Role-based permissions beyond a single admin list.
