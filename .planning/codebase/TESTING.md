# Testing Patterns

**Analysis Date:** 2026-04-24

## Test Framework

**Runner:**
- `pytest` is the test runner used by all files under `tests/`.
- No `pytest.ini`, `pyproject.toml`, `tox.ini`, or coverage config is present.
- `pytest` is missing from `requirements.txt`; install it separately before running the suite.

**Assertion Library:**
- Plain Python `assert` statements are used throughout `tests/test_nonfood_conversation.py`, `tests/test_food_flow_regression.py`, and `tests/test_nonfood_excel_service.py`.
- `unittest.mock.patch` and `MagicMock` appear in legacy `tests/test_bot.py`, but most current tests prefer fakes and `monkeypatch`.

**Run Commands:**
```bash
pytest tests/              # Run all tests
pytest tests/test_nonfood_conversation.py  # Run the main non-food FSM regression file
pytest tests/test_food_flow_regression.py  # Run namespace/wiring regression guards
```

## Test File Organization

**Location:**
- Tests live in `tests/` and use top-level `test_*.py` files.
- `tests/AGENTS.md` is the local test-suite knowledge base and should be read before large test edits.

**Naming:**
- Test modules use `test_<area>.py`: `tests/test_nonfood_conversation.py`, `tests/test_nonfood_repository.py`, `tests/test_nonfood_excel_service.py`.
- Test functions use `test_<behavior>()`, e.g. `test_entry_menu_branches()` and `test_build_order_excel_nonfood_formula_cells_preserved()`.
- Legacy grouped tests in `tests/test_bot.py` use classes such as `TestFmtQty`, `TestGetCategories`, and `TestQtyValidation`.

**Structure:**
```
tests/
├── AGENTS.md                         # Test-suite knowledge base and gotchas
├── test_nonfood_conversation.py       # Main fake-Telegram non-food FSM regression suite
├── test_food_flow_regression.py       # Food/non-food namespace and bot wiring guardrails
├── test_nonfood_bootstrap.py          # Non-food workbook bootstrap fallback contracts
├── test_nonfood_repository.py         # Mongo collection isolation for non-food data
├── test_nonfood_excel_service.py      # Excel generation contracts for non-food workbook
├── test_nonfood_contracts.py          # Source/contract checks for non-food behavior
└── test_bot.py                        # Legacy utility expectations, partly stale
```

## Test Structure

**Suite Organization:**
```python
def test_entry_menu_branches(monkeypatch):
    module = _import_nonfood_entry_module()
    monkeypatch.setattr(data, "get_recent_nonfood_dates", lambda n=7: recent_dates[:n])

    ctx = _FakeContext(user_data={...}, bot_data={"nonfood_enabled": True})
    state = asyncio.run(module.cmd_order_nonfood(_FakeUpdate(message=_FakeMessage()), ctx))

    assert state == OrderStates.NONFOOD_ENTRY_POINT
```

**Patterns:**
- Install fake Telegram modules before importing handlers in `tests/test_nonfood_conversation.py`.
- Exercise async handlers with `asyncio.run(...)`; no `pytest-asyncio` plugin is used.
- Use `monkeypatch` to replace `data.*`, service classes, and bootstrap collaborators instead of reaching live integrations.
- Inspect state transitions, callback data, `ctx.user_data`, and fake reply/edit calls directly.

## Fake Telegram Runtime

**Core Fakes:**
- `_FakeMessage`, `_FakeCallbackQuery`, `_FakeUpdate`, `_FakeContext`, `_FakeInlineKeyboardButton`, and `_FakeInlineKeyboardMarkup` live in `tests/test_nonfood_conversation.py`.
- `_install_telegram_stubs()` injects fake `telegram` and `telegram.ext` modules into `sys.modules`.
- `_import_*_module()` helpers import production handler modules after stubs are installed.

**Use This Pattern For:**
- Handler-flow tests under `handlers/conversation/`.
- Tests that need `telegram.ext.ConversationHandler`, `CallbackQueryHandler`, `MessageHandler`, `CommandHandler`, or `filters` to exist without importing the real Telegram runtime.

**Avoid:**
- Do not import real Telegram classes in unit-style tests when the fake runtime is sufficient.
- Do not add network-bound Telegram bot tests to this suite.

## Mocking

**Framework:**
- `pytest` `monkeypatch` is the preferred mocking mechanism.
- In-memory fake objects are preferred over real databases, R2 clients, or Telegram objects.

**Patterns:**
```python
monkeypatch.setattr(data, "get_nonfood_order", lambda order_date: items_by_iso.get(order_date.isoformat()))
monkeypatch.setattr(data, "list_nonfood_templates", lambda: templates)
```

**What to Mock:**
- Repository seams from `data/__init__.py` and `data/mongodb_repository.py`.
- R2/download seams passed to `_bootstrap_nonfood_assets()` in `bot.py`.
- Excel workbook inputs by building in-memory `openpyxl.Workbook` objects in `tests/test_nonfood_excel_service.py`.
- Telegram runtime modules through `sys.modules` stubs.

**What NOT to Mock:**
- Do not mock state enum values from `states.py`; assert real `OrderStates.*` members.
- Do not mock callback/session namespace strings when tests are intended to catch collisions.
- Do not hit live MongoDB, Cloudflare R2/S3, or Telegram APIs.

## Fixtures and Factories

**Test Data:**
```python
RECENT_ITEMS = [
    {"code": "NF01", "name": "Giấy A4", "qty": 2, "unit": "ram"},
    {"code": "NF02", "name": "Bút bi", "qty": 5, "unit": "cây"},
]
```

**Location:**
- Inline module-level constants in `tests/test_nonfood_conversation.py` hold recent/history/template item sets.
- `_make_nf_workbook()` and `_excel_service_with_fake_wb()` in `tests/test_nonfood_excel_service.py` create minimal in-memory workbook fixtures.
- Repository tests use fake collection/cursor objects in `tests/test_nonfood_repository.py`.

## Regression Areas

**Non-food FSM:**
- `tests/test_nonfood_conversation.py` is the main behavioral source of truth for `/order_nonfood` entry, history, template, search, edit, confirm, and export behavior.
- Preserve Vietnamese-facing strings in assertions when the user-visible copy is contractually important.

**Food vs Non-food Isolation:**
- `tests/test_food_flow_regression.py` protects callback prefix separation, session-key separation, and `bot.py` wiring assumptions.
- Any new non-food callback prefix must be added intentionally and must not collide with food prefixes.

**Bootstrap:**
- `tests/test_nonfood_bootstrap.py` validates non-food workbook bootstrap behavior without real R2/local workbook dependencies.
- `_bootstrap_nonfood_assets()` in `bot.py` has dependency injection seams (`service_cls`, `download_excel_fn`) specifically for these tests.

**Repository:**
- `tests/test_nonfood_repository.py` validates non-food collections stay separate from `orders` and `templates` in `data/mongodb_repository.py`.

**Excel:**
- `tests/test_nonfood_excel_service.py` asserts non-food Excel output writes product code to column B and quantity to column G while preserving formula cells such as columns C and E.

## Coverage

**Requirements:**
- No coverage target is configured.
- No `.coveragerc` or coverage command is present.

**View Coverage:**
```bash
pytest --cov=. tests/      # Requires installing pytest-cov separately; not configured in repo
```

## Test Types

**Unit Tests:**
- Service-level tests cover `ExcelService.build_order_excel_nonfood()` in `tests/test_nonfood_excel_service.py`.
- Repository unit tests isolate `data/mongodb_repository.py` with fake collections in `tests/test_nonfood_repository.py`.

**Integration-Style Handler Tests:**
- `tests/test_nonfood_conversation.py` exercises multiple handler transitions with a fake Telegram runtime and fake `ctx.user_data` / `ctx.bot_data`.
- These tests are deterministic and local; they are not live integration tests.

**Source/Contract Tests:**
- `tests/test_food_flow_regression.py` uses AST/source inspection to avoid importing real Telegram modules while validating handlers and bot wiring.
- `tests/test_nonfood_contracts.py` performs non-food contract checks with source/runtime seams.

**E2E Tests:**
- Not used. There are no tests that run the bot against Telegram or a real deployment.

## Common Patterns

**Async Testing:**
```python
state = asyncio.run(module.handle_nonfood_entry(_FakeUpdate(callback_query=query), ctx))
assert state == OrderStates.NONFOOD_EDITING
```

**Error Testing:**
```python
raw = update.message.text.strip().replace(",", ".")
try:
    qty = float(raw)
except ValueError:
    await update.message.reply_text("⚠️ Nhập số hợp lệ:")
    return OrderStates.ENTERING_EDIT_QTY
```

**AST/Source Testing:**
```python
source = filepath.read_text(encoding="utf-8")
tree = ast.parse(source)
defined = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
```

## Known Caveats and Gaps

- `pytest` is not listed in `requirements.txt`, so a fresh environment needs an extra test dependency install.
- `tests/test_bot.py` expects `fmt_qty` and `get_categories` exports from `bot.py`; this is a legacy/stale expectation relative to the current handler/service split.
- Food flow coverage is lighter than non-food coverage; `tests/test_food_flow_regression.py` mainly protects namespace and wiring contracts rather than full food conversation behavior.
- No coverage thresholds, lint checks, type checks, or CI config were detected.
- `dashboard/` has no active test coverage and should not be treated as a live app until dashboard source files are restored.

---

*Testing analysis: 2026-04-24*
