# Coding Conventions

**Analysis Date:** 2026-04-24

## Naming Patterns

**Files:**
- Use lowercase snake_case Python modules: `bot.py`, `states.py`, `services/excel_service.py`, `data/mongodb_repository.py`.
- Keep mirrored food/non-food flow files paired: `handlers/conversation/entry.py` with `handlers/conversation/nonfood_entry.py`, `category.py` with `nonfood_category.py`, `confirm.py` with `nonfood_confirm.py`, `template.py` with `nonfood_template.py`.
- Treat `db.py` and `r2.py` as deprecated compatibility shims; put new persistence/storage logic in `data/mongodb_repository.py` and `data/r2_storage.py`.

**Functions:**
- Use `snake_case` for functions and helpers: `_bootstrap_nonfood_assets()` in `bot.py`, `_reset_nonfood_session()` in `handlers/conversation/nonfood_entry.py`, `_get_workbook()` in `services/excel_service.py`.
- Prefix module-private helpers with `_`: `_fmt_qty()` in `handlers/conversation/editing.py`, `_orders()` and `_nonfood_orders()` in `data/mongodb_repository.py`.
- Telegram command handlers use `cmd_*`; callback/message handlers use `handle_*`, `receive_*`, or `show_*`, e.g. `cmd_order_nonfood()`, `handle_nonfood_entry()`, `show_edit_screen()`.

**Variables:**
- Use `snake_case` for locals and `UPPER_SNAKE_CASE` for process constants: `TOKEN`, `EXCEL_PATH`, `NONFOOD_EXCEL_PATH`, `ALLOWED_USER_IDS`, `EXCEL_BUFFER` in `bot.py`.
- Keep food session keys unprefixed (`order`, `order_date`, `current_cat`, `editing_code`) and non-food session keys explicitly prefixed (`nonfood_order`, `nonfood_order_date`, `nf_current_cat`, `nf_editing_code`) as enforced by `tests/test_food_flow_regression.py`.
- Keep callback namespaces disjoint: food uses `en:`, `hi:`, `ei:`, `eq:`, `cat:`, `item:`, `qdate:`; non-food uses `nfe:`, `nfh:`, `nfei:`, `nfeq:`, `nfcat:`, `nfitem:`, `nfqdate:`, `nftpl:`, `nfsearch:`.

**Types:**
- Use `PascalCase` for classes and dataclasses: `ExcelService`, `ExcelConfig`, `OrderItem`, `FoodItem`.
- Use local aliases for repeated dict contracts, e.g. `Item = dict[str, Any]` and `OrderMap = dict[str, Item]` in `handlers/conversation/nonfood_entry.py`.

## Code Style

**Formatting:**
- No formatter config is present: no `pyproject.toml`, `ruff.toml`, `.prettierrc`, or `pytest.ini` detected.
- Prefer readable multi-line imports and calls for new code. `bot.py` has compact imports and occasional semicolon use; do not spread that pattern further.
- Preserve Vietnamese user-facing strings and comments where the surrounding flow is Vietnamese.

**Linting:**
- No formal linter is configured.
- Some intentional import-order exceptions exist in `handlers/conversation/nonfood_editing.py` with `# noqa: E402`; do not remove deferred imports unless circular dependencies are addressed.

## Import Organization

**Order:**
1. Standard library imports: `os`, `sys`, `logging`, `io`, `functools`, `datetime`, `typing`, `pathlib`.
2. Third-party imports: `telegram`, `telegram.ext`, `openpyxl`, `pymongo`, `boto3`, `dotenv`.
3. Project imports from repo root: `states`, `services.*`, `handlers.*`, `data.*`, `models.*`.

**Path Aliases:**
- No package alias system is configured. Use absolute imports from repository root such as `from states import OrderStates` and `from services.excel_service import ExcelService`.
- Tests add the repo root to `sys.path` with `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`, e.g. `tests/test_nonfood_conversation.py`.

## Async Handler Patterns

- Telegram handlers are `async def` and return `OrderStates.*` members or `ConversationHandler.END`, e.g. `handlers/conversation/nonfood_entry.py` and `handlers/conversation/editing.py`.
- Always `await` Telegram methods: `message.reply_text(...)`, `message.edit_text(...)`, `query.answer(...)`.
- Use `assert query is not None` / `assert message is not None` after selecting the expected Telegram update shape, then continue with typed code.
- Keep state transitions explicit; do not return raw integer state IDs from new handler code.

## Type Hints

- Prefer modern Python 3.11 union syntax: `io.BytesIO | None`, `dict[str, object]`, `list[dict]`, as used in `bot.py` and `services/excel_service.py`.
- Use `from __future__ import annotations` in modules that benefit from postponed annotations, as seen in `services/excel_service.py`, `data/mongodb_repository.py`, and most non-food tests.
- Use `typing.cast()` around `ctx.user_data` / `ctx.bot_data` when narrowing Telegram context data, e.g. `handlers/conversation/nonfood_entry.py`.

## Error Handling

**Patterns:**
- Use guard returns for disabled or empty flows: `cmd_order_nonfood()` returns `ConversationHandler.END` when `nonfood_enabled` is false, and `done_editing()` returns to `OrderStates.EDITING` for empty orders.
- Log integration/bootstrap failures and fall back where possible: `_bootstrap_nonfood_assets()` in `bot.py` tries R2 first, then local workbook, then disables the non-food flow.
- For user input validation, reply in Vietnamese and remain in the same state for invalid data; see `receive_edit_qty()` in `handlers/conversation/editing.py`.
- Avoid broad exception swallowing in new code. Existing broad catches are mostly Telegram edit-vs-reply fallback and integration/bootstrap boundaries.

## Logging

**Framework:** Python `logging`.

**Patterns:**
- Define `logger = logging.getLogger(__name__)` at module level in service/integration modules such as `bot.py`, `services/excel_service.py`, and `data/r2_storage.py`.
- Configure logging once in `bot.py` via `logging.basicConfig(...)`.
- Use structured `%s` interpolation for log messages where practical, as in `_bootstrap_nonfood_assets()` in `bot.py`.
- Use `logger.exception(...)` for caught exceptions where stack traces matter.

## Comments

**When to Comment:**
- Use comments for workflow-sensitive or Excel-layout-specific behavior, e.g. row/column annotations in `services/excel_service.py`.
- Vietnamese comments are normal in business logic and tests; preserve them when editing adjacent code.
- Keep callback and session namespace comments explicit because food/non-food collisions are regression risks.

**JSDoc/TSDoc:**
- Not applicable. Use Python docstrings for public classes, handlers, and services.

## Function Design

**Size:**
- Small handlers and helpers are preferred, but conversation orchestration modules can be longer when state transitions are cohesive.
- Put reusable screen rendering in helpers such as `show_edit_screen()` / `_show_nonfood_edit_screen()` instead of duplicating keyboard construction across handlers.

**Parameters:**
- Telegram handlers take `(update: Update, ctx: ContextTypes.DEFAULT_TYPE)`.
- Services accept explicit dependencies at construction or function parameters. `_bootstrap_nonfood_assets()` accepts `service_cls` and `download_excel_fn` seams for tests.

**Return Values:**
- Handler returns should be conversation states: `OrderStates.EDITING`, `OrderStates.NONFOOD_ENTRY_POINT`, or `ConversationHandler.END`.
- Data repository functions return plain dict/list values for persistence boundaries, e.g. `get_nonfood_order()` in `data/mongodb_repository.py`.

## Module Design

**Exports:**
- Modules export functions directly; no `__all__` pattern is used.
- `data/__init__.py` re-exports repository functions for handlers to import as `import data`.
- Root `db.py` and `r2.py` are backward-compatibility shims only.

**Barrel Files:**
- `handlers/__init__.py` and `data/__init__.py` serve as lightweight barrels. Keep them aligned when adding public handlers or repository functions.

## Project-Specific Anti-Patterns

- Do not read or commit `.env`; environment values are loaded through `dotenv` and `os.environ` in `bot.py` and integration modules.
- Do not add live MongoDB or R2 calls to tests; use monkeypatch seams and fake clients.
- Do not blur food and non-food callback/session namespaces; `tests/test_food_flow_regression.py` treats collisions as regressions.
- Do not place new active code under `dashboard/` until dashboard sources are restored and documented.
- Do not hardcode stale state counts; `states.py` is the source of truth for all `OrderStates` members.

---

*Convention analysis: 2026-04-24*
