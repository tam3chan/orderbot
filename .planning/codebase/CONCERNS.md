# Codebase Concerns

**Analysis Date:** 2026-04-24

## Severity Summary

- **High:** Production startup depends on local/R2 Excel templates and MongoDB with limited health validation; non-food Excel export silently drops items beyond template capacity.
- **Medium:** Food/non-food conversation flows are mirrored manually across many files, creating callback/session-state fragility; docs and tests are out of sync with current architecture.
- **Low:** Deprecated shim modules and generated caches clutter the repository and increase confusion for future maintainers.

## Tech Debt

**Mirrored food/non-food flow duplication:**
- Severity: Medium
- Issue: Food and non-food flows duplicate state-machine patterns across sibling modules instead of sharing common abstractions.
- Files: `handlers/conversation/editing.py`, `handlers/conversation/confirm.py`, `handlers/conversation/category.py`, `handlers/conversation/template.py`, `handlers/conversation/nonfood_editing.py`, `handlers/conversation/nonfood_confirm.py`, `handlers/conversation/nonfood_category.py`, `handlers/conversation/nonfood_template.py`
- Impact: Fixes must be inspected and often applied twice. Callback prefix and session-key mistakes can break one flow while tests pass for the other.
- Fix approach: Extract shared pure helpers for quantity parsing, date parsing, confirmation rendering, and item formatting while preserving separate callback namespaces.

**Non-food orchestration hub has many cross-module imports:**
- Severity: Medium
- Issue: `handlers/conversation/nonfood_editing.py` imports handlers from entry, category, search, template, and confirm modules at module import time with `# noqa: E402` comments.
- Files: `handlers/conversation/nonfood_editing.py`
- Impact: The module is fragile to import-order changes and makes circular dependency risk easy to reintroduce.
- Fix approach: Keep state wiring centralized, but move pure helpers and nested handler definitions into smaller import-safe modules; document intentional late imports when they are necessary.

**Deprecated compatibility shims remain in active root:**
- Severity: Low
- Issue: `db.py` and `r2.py` re-export new data-layer modules with deprecation warnings.
- Files: `db.py`, `r2.py`, `data/mongodb_repository.py`, `data/r2_storage.py`
- Impact: New code may accidentally import deprecated paths, and import-time warnings can confuse test output.
- Fix approach: Keep shims only if external deployments depend on them; otherwise remove after grepping all internal imports and updating docs.

**Hard-coded workbook assumptions:**
- Severity: Medium
- Issue: Excel row, column, sheet, and capacity assumptions are embedded in `ExcelConfig` without external validation or schema documentation.
- Files: `services/excel_service.py`
- Impact: Template edits can break item loading or order export at runtime, and failures surface only when the bot starts or a user confirms an order.
- Fix approach: Add workbook validation that checks required sheets, columns, template row ranges, and capacity during startup with clear operator-facing errors.

## Known Bugs / Behavior Risks

**Non-food orders beyond template capacity are silently truncated:**
- Severity: High
- Symptoms: `build_order_excel_nonfood()` logs a warning when item count exceeds the configured 11 rows, then stops writing extra items.
- Files: `services/excel_service.py`
- Trigger: A non-food order with more than `ExcelConfig.nonfood_out_item_end - nonfood_out_item_start + 1` items.
- Workaround: Keep non-food orders within the template capacity.
- Fix approach: Reject oversized non-food orders before confirmation, generate additional rows preserving formulas, or split output into multiple sheets/files.

**Food order export mutates template rows in a narrow hard-coded way:**
- Severity: Medium
- Symptoms: Food export deletes rows `19..24`, then inserts rows from template row `18` based on order length.
- Files: `services/excel_service.py`
- Trigger: Template layout changes, formula ranges move, or the order has edge-case item counts.
- Workaround: Keep `PR NOODLE` template shape aligned with current row assumptions.
- Fix approach: Replace magic row deletion with named configuration and validation tests against representative workbook fixtures.

**Legacy test module imports missing `bot.py` exports:**
- Severity: Medium
- Symptoms: `tests/test_bot.py` imports `fmt_qty` and `get_categories` from `bot.py`, but current formatting/grouping helpers live elsewhere or are private.
- Files: `tests/test_bot.py`, `bot.py`, `handlers/conversation/editing.py`, `handlers/conversation/nonfood_editing.py`, `services/excel_service.py`
- Trigger: Running the full test suite with `pytest tests/`.
- Workaround: Run targeted non-food regression tests while legacy tests are updated.
- Fix approach: Either restore supported public utility functions or rewrite `tests/test_bot.py` around current service/handler contracts.

**Invalid preset callback values are swallowed:**
- Severity: Low
- Symptoms: Quantity preset handlers catch `ValueError` and continue without notifying users.
- Files: `handlers/conversation/editing.py`, `handlers/conversation/nonfood_editing.py`
- Trigger: Malformed callback data matching `eq:` or `nfeq:` patterns.
- Workaround: Callback data is generated internally, so normal users should not hit this.
- Fix approach: Log invalid callback payloads and return a user-visible retry message for corrupted state.

## Security Considerations

**Optional whitelist can leave bot open to every Telegram user with access to the bot:**
- Severity: High
- Risk: If `ALLOWED_USER_IDS` is unset or empty, `authorized_only()` allows all users.
- Files: `bot.py`
- Current mitigation: When configured, `ALLOWED_USER_IDS` rejects non-whitelisted users.
- Recommendations: Make the whitelist required in production, fail startup when absent unless an explicit `ALLOW_PUBLIC_BOT=true` is set, and wrap every command entry point consistently.

**Authorization wrapper is defined but not applied at handler registration:**
- Severity: Medium
- Risk: `authorized_only()` exists, but command handlers are registered directly in `main()`.
- Files: `bot.py`
- Current mitigation: None detected at registration sites.
- Recommendations: Wrap command callbacks and conversation entry points with `authorized_only()` or enforce authorization via a global handler/filter.

**Secrets are environment-driven but `.env` exists locally:**
- Severity: Medium
- Risk: `.env` is present in the working tree and must never be read or committed.
- Files: `.env`, `.gitignore`, `bot.py`, `data/mongodb_repository.py`, `data/r2_storage.py`
- Current mitigation: `.gitignore` excludes `.env`, and code reads credentials from environment variables.
- Recommendations: Keep `.env` untracked, add a safe `.env.example`, and audit git history before sharing the repository.

**MongoDB writes accept raw item dictionaries from session state:**
- Severity: Medium
- Risk: User/session data is persisted directly to MongoDB without schema validation.
- Files: `data/mongodb_repository.py`, `handlers/conversation/confirm.py`, `handlers/conversation/nonfood_confirm.py`
- Current mitigation: Item choices usually originate from parsed Excel catalogs.
- Recommendations: Validate order item shape before `save_order()` and `save_nonfood_order()`; reject unexpected keys and non-numeric quantities.

## Reliability Issues

**Startup has multiple hard dependencies with limited graceful degradation:**
- Severity: High
- Problem: Bot startup requires `BOT_TOKEN`, food workbook availability, and valid workbook sheets. MongoDB is not pinged at startup.
- Files: `bot.py`, `services/excel_service.py`, `data/mongodb_repository.py`
- Impact: Missing or changed templates fail startup; MongoDB failures surface later during user confirmation/history flows.
- Fix approach: Add startup health checks for Excel, MongoDB, and optional R2 with explicit readiness logs and fail-fast behavior for required services.

**R2 food template bootstrap only checks partial configuration:**
- Severity: Medium
- Problem: `_init_excel_buffer()` checks `R2_ENDPOINT` and `R2_ACCESS_KEY`, then `download_excel()` requires `R2_SECRET_KEY` and may raise if missing.
- Files: `bot.py`, `data/r2_storage.py`
- Cause: Food R2 configuration detection is less strict than non-food detection.
- Improvement path: Use the same `all(os.environ.get(k) for k in (...))` check for both food and non-food R2 bootstraps.

**Database collection index creation happens on every collection access:**
- Severity: Low
- Problem: `_orders()` and `_nonfood_orders()` call `create_index()` every time collection accessors are used.
- Files: `data/mongodb_repository.py`
- Cause: Index setup is embedded in repository accessor functions.
- Improvement path: Move index creation to an explicit startup migration/init function.

**No retry/backoff around network integrations:**
- Severity: Medium
- Problem: MongoDB writes and R2 downloads are single-attempt operations from handler/startup code.
- Files: `data/mongodb_repository.py`, `data/r2_storage.py`, `handlers/conversation/confirm.py`, `handlers/conversation/nonfood_confirm.py`
- Cause: Direct driver/client calls without retry policy.
- Improvement path: Add bounded retries for transient R2/Mongo errors and keep user-visible failure states recoverable.

## Performance Bottlenecks

**Workbook parsing and generation are synchronous:**
- Severity: Medium
- Problem: `openpyxl` parsing and workbook save operations run synchronously inside bot startup and async handler paths.
- Files: `services/excel_service.py`, `handlers/conversation/confirm.py`, `handlers/conversation/nonfood_confirm.py`
- Cause: CPU/file work is executed directly in async Telegram handlers.
- Improvement path: Offload heavy workbook generation to a thread executor if file size or user count grows.

**Large inline keyboards can become unwieldy:**
- Severity: Low
- Problem: Category and edit screens build Telegram inline keyboards from in-memory order/category data.
- Files: `handlers/conversation/editing.py`, `handlers/conversation/nonfood_category.py`, `handlers/conversation/nonfood_editing.py`, `keyboards/inline.py`
- Cause: No pagination concerns are visible in the central edit screen for large orders.
- Improvement path: Keep category pagination/search contracts covered by tests and add pagination for large edit summaries if Telegram limits are hit.

## Fragile Areas

**Conversation state and callback namespace wiring:**
- Severity: High
- Files: `bot.py`, `states.py`, `handlers/conversation/nonfood_editing.py`, `handlers/conversation/nonfood_category.py`, `handlers/conversation/nonfood_search.py`, `tests/test_food_flow_regression.py`, `tests/test_nonfood_contracts.py`
- Why fragile: Nested `ConversationHandler`s rely on exact callback prefixes, parent/child state mappings, and separate food/non-food session keys.
- Safe modification: Before changing callback data or state returns, inspect sibling food/non-food modules and update regression tests for namespace separation.
- Test coverage: Strongest for non-food flow; food flow has lighter regression coverage.

**Excel workbook contract:**
- Severity: High
- Files: `services/excel_service.py`, `ORDER NONFOOD MIN xlsx.xlsx`, `tests/test_nonfood_excel_service.py`
- Why fragile: Behavior depends on exact workbook sheet names (`Food T01`, `PR NOODLE`, `CCDC`, `VTTH`) and hard-coded row/column positions.
- Safe modification: Add or update fixture workbooks and assert representative output cells before changing row/column constants.
- Test coverage: Non-food generation has focused tests; food workbook generation needs equivalent coverage.

**Session clearing can remove unrelated user data in food flow:**
- Severity: Medium
- Files: `handlers/conversation/confirm.py`
- Why fragile: Food confirm/cancel calls `ctx.user_data.clear()`, while non-food flow carefully removes only `NONFOOD_SESSION_KEYS`.
- Safe modification: Use explicit food session keys to avoid deleting unrelated per-user state as features grow.
- Test coverage: Non-food session-key isolation is covered; food session clearing behavior is less protected.

## Scaling Limits

**Single-process polling deployment:**
- Severity: Medium
- Current capacity: One `Application.run_polling()` process handles bot traffic.
- Limit: Scaling horizontally with polling can duplicate message handling unless only one replica is active.
- Files: `bot.py`, `Dockerfile`
- Scaling path: Move to webhook-based deployment or enforce a single replica/worker in the hosting platform.

**One order per date per collection:**
- Severity: Medium
- Current capacity: `orders.date` and `nonfood_orders.date` are unique across the entire database.
- Limit: Multiple users or departments cannot store separate orders for the same date.
- Files: `data/mongodb_repository.py`
- Scaling path: Include user/tenant/location in unique keys and repository query filters.

## Dependencies at Risk

**Test dependency missing from runtime requirements:**
- Severity: Medium
- Risk: `pytest` is imported by tests but absent from `requirements.txt`.
- Files: `requirements.txt`, `tests/test_bot.py`
- Impact: Fresh environments cannot run the documented `pytest tests/` command without manually installing pytest.
- Migration plan: Add a dev requirements file such as `requirements-dev.txt` or add pytest to project tooling docs.

**No formal lint/type tooling configured:**
- Severity: Low
- Risk: There is no detected `pyproject.toml`, Ruff, Black, mypy, or pytest config.
- Files: `requirements.txt`, repository root
- Impact: Style/type regressions rely on human review and tests only.
- Migration plan: Add minimal Ruff formatting/lint config and a test command in project docs.

## Missing Critical Features

**Environment template referenced by docs is missing:**
- Severity: Medium
- Problem: `README.md` instructs `cp .env.example .env`, but `.env.example` is not present in the repository listing.
- Files: `README.md`, `.gitignore`
- Blocks: New deployers cannot reliably discover required variables without reading code.
- Next step: Add `.env.example` with variable names only and no secret values.

**Operational health checks are absent from deployment image:**
- Severity: Medium
- Problem: `Dockerfile` only runs `python bot.py` and defines no healthcheck.
- Files: `Dockerfile`, `bot.py`
- Blocks: Hosting platforms cannot distinguish a healthy polling loop from a hung process using container metadata alone.
- Next step: Add an application-level heartbeat/logging strategy or platform-specific health check if deployment target supports it.

**README is stale relative to current code:**
- Severity: Medium
- Problem: `README.md` describes a 12-state bot, root `db.py`/`r2.py`, and lacks `/order_nonfood` documentation.
- Files: `README.md`, `states.py`, `db.py`, `r2.py`, `handlers/conversation/nonfood_editing.py`
- Blocks: New contributors may follow outdated architecture and add code in deprecated locations.
- Next step: Update README to match `AGENTS.md` and current food/non-food architecture.

## Test Coverage Gaps

**Food flow is less covered than non-food flow:**
- Severity: Medium
- What's not tested: End-to-end food handler state transitions, food Excel generation, and food session cleanup have less direct coverage than non-food equivalents.
- Files: `handlers/conversation/entry.py`, `handlers/conversation/category.py`, `handlers/conversation/editing.py`, `handlers/conversation/confirm.py`, `tests/test_food_flow_regression.py`
- Risk: Mirrored behavior can diverge silently.
- Priority: High

**Integration tests avoid real MongoDB/R2:**
- Severity: Low
- What's not tested: Live connection string handling, R2 object download behavior, and MongoDB index creation against real services.
- Files: `data/mongodb_repository.py`, `data/r2_storage.py`, `tests/test_nonfood_repository.py`, `tests/test_nonfood_bootstrap.py`
- Risk: Production-only configuration or credential errors appear after deployment.
- Priority: Medium

**Legacy test expectations are stale:**
- Severity: Medium
- What's not tested: Current public API boundaries are not reflected by `tests/test_bot.py`.
- Files: `tests/test_bot.py`, `bot.py`
- Risk: Full-suite failures reduce trust in test results and encourage skipping tests.
- Priority: High

## Repository Hygiene / Deployment Concerns

**Generated caches are present in the working tree:**
- Severity: Low
- Issue: `__pycache__` files are visible across source, tests, and dashboard directories.
- Files: `__pycache__/`, `services/__pycache__/`, `handlers/__pycache__/`, `data/__pycache__/`, `dashboard/__pycache__/`
- Impact: Noise during exploration and risk of stale bytecode artifacts being copied into Docker image via `COPY . .`.
- Fix approach: Keep caches ignored and remove tracked/generated cache artifacts from the repository and Docker build context.

**Dashboard scaffolding appears non-deployable:**
- Severity: Low
- Issue: Dashboard directories/caches exist, but active dashboard source files are not present in the current source listing.
- Files: `dashboard/`, `Dockerfile`, `AGENTS.md`
- Impact: Contributors may assume a dashboard app exists when only the bot is deployable.
- Fix approach: Remove stale dashboard artifacts or restore documented dashboard source with separate deployment instructions.

**Docker image copies local-only artifacts unless excluded by build context:**
- Severity: Medium
- Issue: `Dockerfile` uses `COPY . .`; without `.dockerignore`, local files such as `.env`, `.venv`, `.planning`, caches, and workbooks may enter build context even if ignored by git.
- Files: `Dockerfile`, `.gitignore`, `.env`, `.venv/`, `.planning/`
- Impact: Larger images and potential accidental secret/artifact inclusion during local builds.
- Fix approach: Add `.dockerignore` mirroring secret/generated/local-only paths.

---

*Concerns audit: 2026-04-24*
