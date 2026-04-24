# Codebase Structure

**Analysis Date:** 2026-04-24

## Directory Layout

```text
order_bot/
├── bot.py                         # Bot entry point and handler wiring
├── states.py                      # Shared 25-state OrderStates enum
├── db.py                          # Deprecated MongoDB shim to data.mongodb_repository
├── r2.py                          # Deprecated R2 shim to data.r2_storage
├── requirements.txt               # Runtime Python dependencies
├── Dockerfile                     # Container entry running python bot.py
├── AGENTS.md                      # Project knowledge base for agents
├── data/                          # MongoDB repository and R2 storage adapters
├── handlers/                      # Telegram command and conversation handlers
├── keyboards/                     # Inline keyboard helper builders
├── models/                        # Dataclass model helpers
├── services/                      # Excel and order services
├── tests/                         # Pytest regression suite and Telegram fakes
├── dashboard/                     # Scaffold/cache-only dashboard area
└── .planning/                     # GSD planning artifacts and generated maps
```

## Directory Purposes

**Root files:**
- Purpose: Runtime entry, global state enum, compatibility shims, deployment metadata.
- Contains: `bot.py`, `states.py`, `db.py`, `r2.py`, `requirements.txt`, `Dockerfile`, `README.md`, `AGENTS.md`.
- Key files: `bot.py`, `states.py`.

**`handlers/`:**
- Purpose: Telegram command handlers and conversation-state handlers.
- Contains: top-level commands in `handlers/start.py`, `handlers/list.py`, `handlers/search.py`, `handlers/cancel.py`, plus FSM modules under `handlers/conversation/`.
- Key files: `handlers/conversation/entry.py`, `handlers/conversation/editing.py`, `handlers/conversation/nonfood_editing.py`.

**`handlers/conversation/`:**
- Purpose: Food and non-food finite-state conversation flows.
- Contains: mirrored modules for entry, category browsing, edit hub, templates, confirmation/export, and non-food search.
- Key files: `handlers/conversation/category.py`, `handlers/conversation/confirm.py`, `handlers/conversation/nonfood_category.py`, `handlers/conversation/nonfood_confirm.py`.

**`services/`:**
- Purpose: Business services that process orders and Excel workbooks.
- Contains: `services/excel_service.py`, `services/order_service.py`, `services/__init__.py`.
- Key files: `services/excel_service.py`.

**`data/`:**
- Purpose: Database and object-storage integration layer.
- Contains: `data/mongodb_repository.py`, `data/r2_storage.py`, `data/__init__.py`.
- Key files: `data/mongodb_repository.py`, `data/r2_storage.py`.

**`models/`:**
- Purpose: Dataclass model helpers and dict conversion methods.
- Contains: `models/order.py`, `models/food_item.py`, `models/__init__.py`.
- Key files: `models/order.py`, `models/food_item.py`.

**`keyboards/`:**
- Purpose: Reusable inline keyboard builders for food callback namespaces.
- Contains: `keyboards/inline.py`, `keyboards/__init__.py`.
- Key files: `keyboards/inline.py`.

**`tests/`:**
- Purpose: Pytest regression coverage with fake Telegram runtime objects.
- Contains: `tests/test_bot.py`, `tests/test_food_flow_regression.py`, `tests/test_nonfood_conversation.py`, `tests/test_nonfood_contracts.py`, `tests/test_nonfood_excel_service.py`, `tests/test_nonfood_repository.py`, `tests/test_nonfood_bootstrap.py`, `tests/AGENTS.md`.
- Key files: `tests/test_nonfood_conversation.py`, `tests/test_food_flow_regression.py`.

**`dashboard/`:**
- Purpose: Placeholder/scaffold area for a dashboard.
- Contains: observed `__pycache__` artifacts and skeleton directories only.
- Key files: no active dashboard source files detected.

## Key File Locations

**Entry Points:**
- `bot.py`: Main process entry, environment loading, Excel bootstrap, `Application` creation, handler registration.
- `handlers/conversation/entry.py::cmd_order()`: Food `/order` entry.
- `handlers/conversation/nonfood_entry.py::cmd_order_nonfood()`: Non-food `/order_nonfood` entry.
- `handlers/conversation/nonfood_editing.py::nonfood_conv`: Top-level non-food `ConversationHandler`.

**Configuration:**
- `requirements.txt`: Python package dependencies.
- `Dockerfile`: Container runtime command for `python bot.py`.
- `states.py`: State IDs used as handler state-map keys.
- `AGENTS.md`: Project guidance and known conventions.

**Core Logic:**
- `handlers/conversation/entry.py`: Food entry menu, recent order, template selection, history date selection.
- `handlers/conversation/editing.py`: Food edit hub and quantity-edit keypad.
- `handlers/conversation/category.py`: Food category browsing and item quantity input nested handler.
- `handlers/conversation/confirm.py`: Food confirmation, date selection, Excel generation, MongoDB save.
- `handlers/conversation/template.py`: Food template save/load flow.
- `handlers/conversation/nonfood_entry.py`: Non-food entry/history/session initialization.
- `handlers/conversation/nonfood_editing.py`: Non-food top-level router and edit hub.
- `handlers/conversation/nonfood_category.py`: Non-food category browsing and edit-screen rendering.
- `handlers/conversation/nonfood_search.py`: Non-food exact-code search subflow.
- `handlers/conversation/nonfood_confirm.py`: Non-food confirmation, date selection, Excel generation, MongoDB save.
- `handlers/conversation/nonfood_template.py`: Non-food template save/load flow.
- `services/excel_service.py`: Excel catalog parsing and workbook generation.
- `data/mongodb_repository.py`: MongoDB persistence functions for orders and templates.
- `data/r2_storage.py`: R2 workbook download function.

**Testing:**
- `tests/test_bot.py`: Bot bootstrap and command wiring coverage.
- `tests/test_food_flow_regression.py`: Food flow callback/state regression coverage.
- `tests/test_nonfood_conversation.py`: Non-food FSM regression coverage.
- `tests/test_nonfood_contracts.py`: Non-food callback/session contract coverage.
- `tests/test_nonfood_excel_service.py`: Non-food workbook parsing/output coverage.
- `tests/test_nonfood_repository.py`: Non-food MongoDB repository coverage.
- `tests/test_nonfood_bootstrap.py`: Non-food asset bootstrap coverage.
- `tests/AGENTS.md`: Test-specific fake Telegram patterns and regression guidance.

## Important Symbols and Modules

**Runtime composition:**
- `bot.py::main()`: Build and run the Telegram application.
- `bot.py::_build_bot_data()`: Create shared `bot_data` dependency contract.
- `bot.py::_bootstrap_nonfood_assets()`: Load non-food workbook/catalogs and enable/disable non-food feature data.
- `bot.py::post_init()`: Register bot commands, including `/order_nonfood` when non-food is enabled.

**State machine:**
- `states.py::OrderStates`: Enum containing all food and non-food states.
- `handlers/conversation/category.py::category_conv`: Food nested category browser.
- `handlers/conversation/template.py::template_conv`: Food nested template flow.
- `handlers/conversation/nonfood_editing.py::nonfood_conv`: Non-food top-level conversation.
- `handlers/conversation/nonfood_category.py::nonfood_category_conv`: Non-food nested category browser.
- `handlers/conversation/nonfood_search.py::nonfood_search_conv`: Non-food nested exact-code search.

**Services and persistence:**
- `services/excel_service.py::ExcelConfig`: Workbook sheet/column/row layout constants.
- `services/excel_service.py::ExcelService`: Load catalogs and generate food/non-food workbook bytes.
- `services/order_service.py::OrderService`: Order orchestration wrapper around DB and Excel service.
- `data/mongodb_repository.py::get_client()`: Singleton `MongoClient` factory.
- `data/mongodb_repository.py::save_order()` / `save_nonfood_order()`: Date-keyed MongoDB upserts.
- `data/r2_storage.py::download_excel()`: Download workbook object into `io.BytesIO`.

## State Machine Organization

**Food states in `states.py`:**
- Entry/history: `OrderStates.ENTRY_POINT`, `OrderStates.CHOOSING_HISTORY`, `OrderStates.ENTERING_HISTORY_DATE`.
- Edit hub: `OrderStates.EDITING`, `OrderStates.EDITING_ITEM`, `OrderStates.ENTERING_EDIT_QTY`.
- Browse/add item: `OrderStates.CHOOSING_CAT`, `OrderStates.CHOOSING_ITEM`, `OrderStates.ENTERING_QTY`.
- Confirm/date/template: `OrderStates.CONFIRM_ORDER`, `OrderStates.ENTERING_DATE`, `OrderStates.ENTERING_TEMPLATE_NAME`.
- Parent wiring: `bot.py` owns the food parent `ConversationHandler`; add new food states there unless they belong inside a nested child handler.

**Non-food states in `states.py`:**
- Entry/history: `OrderStates.NONFOOD_ENTRY_POINT`, `OrderStates.NONFOOD_CHOOSING_HISTORY`, `OrderStates.NONFOOD_ENTERING_HISTORY_DATE`.
- Edit hub: `OrderStates.NONFOOD_EDITING`, `OrderStates.NONFOOD_EDITING_ITEM`, `OrderStates.NONFOOD_ENTERING_EDIT_QTY`.
- Browse/search/add item: `OrderStates.NONFOOD_CHOOSING_CAT`, `OrderStates.NONFOOD_CHOOSING_ITEM`, `OrderStates.NONFOOD_ENTERING_QTY`, `OrderStates.NONFOOD_SEARCHING`.
- Confirm/date/template: `OrderStates.NONFOOD_CONFIRM_ORDER`, `OrderStates.NONFOOD_ENTERING_DATE`, `OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME`.
- Parent wiring: `handlers/conversation/nonfood_editing.py::nonfood_conv` owns top-level non-food routing.

**Callback namespaces:**
- Food entry/history callbacks use `en:` and `hi:` in `handlers/conversation/entry.py`.
- Food edit callbacks use `ei:` and `eq:` in `handlers/conversation/editing.py`.
- Food category callbacks use `cat:` and `item:` in `handlers/conversation/category.py`.
- Food confirm/date callbacks use `confirm_yes`, `confirm_no`, `back_to_edit`, `change_date`, and `qdate:` in `handlers/conversation/confirm.py`.
- Non-food entry/history callbacks use `nfe:` and `nfh:` in `handlers/conversation/nonfood_entry.py`.
- Non-food edit callbacks use `nfei:`, `nfe:`, and `nfeq:` in `handlers/conversation/nonfood_editing.py` and `nonfood_confirm.py`.
- Non-food browse/search/template callbacks use `nf:`, `nfcat:`, `nfitem:`, `nfsearch:`, `nftpl:`, and `nfqdate:` in non-food modules.

## Mirrored Food/Non-Food Flow Overview

**Food flow module map:**
- Entry/history: `handlers/conversation/entry.py`.
- Category browse: `handlers/conversation/category.py`.
- Edit hub: `handlers/conversation/editing.py`.
- Template save/load: `handlers/conversation/template.py`.
- Confirm/date/export: `handlers/conversation/confirm.py`.
- Session keys: `order`, `order_date`, `editing_code`, `current_cat`, `current_item` in `ctx.user_data`.
- Catalog keys: `items`, `categories`, `excel_service`, `order_service` in `ctx.bot_data`.

**Non-food flow module map:**
- Entry/history: `handlers/conversation/nonfood_entry.py`.
- Category browse: `handlers/conversation/nonfood_category.py`.
- Exact-code search: `handlers/conversation/nonfood_search.py`.
- Edit hub and top-level wiring: `handlers/conversation/nonfood_editing.py`.
- Template save/load: `handlers/conversation/nonfood_template.py`.
- Confirm/date/export: `handlers/conversation/nonfood_confirm.py`.
- Session keys: `nonfood_order`, `nonfood_order_date`, `nf_editing_code`, `nf_current_cat`, `nf_current_item` and siblings in `NONFOOD_SESSION_KEYS`.
- Catalog keys: `nonfood_enabled`, `nonfood_items`, `nonfood_categories`, `nonfood_excel_service`, `nonfood_order_service` in `ctx.bot_data`.

**Mirroring rule:**
- When changing a food handler, inspect the corresponding non-food module before deciding the change is food-only.
- When changing a non-food handler, preserve separate callback prefixes and dedicated session keys to avoid collisions with food flow.

## Naming Conventions

**Files:**
- Handler modules use lowercase snake_case: `handlers/conversation/nonfood_confirm.py`.
- Tests use `test_*.py`: `tests/test_nonfood_conversation.py`.
- Compatibility shims are short root modules: `db.py`, `r2.py`.

**Directories:**
- Feature/layer directories use lowercase plural names: `handlers/`, `services/`, `models/`, `data/`, `keyboards/`, `tests/`.
- Conversation handlers live under `handlers/conversation/`; do not add new FSM modules at repository root.

## Where to Add New Code

**New Telegram command:**
- Primary code: add a module/function under `handlers/`, such as `handlers/report.py`.
- Wiring: register the command in `bot.py::main()` and, if user-facing, update `bot.py::post_init()` bot commands.
- Tests: add or extend `tests/test_bot.py` and command-specific tests under `tests/`.

**New food conversation step:**
- Primary code: add to the matching module in `handlers/conversation/` or create a focused sibling module there.
- State: add enum member to `states.py` only when no existing state fits.
- Wiring: update the parent `ConversationHandler` in `bot.py` or the relevant nested handler such as `handlers/conversation/category.py::category_conv`.
- Tests: extend `tests/test_food_flow_regression.py`.

**New non-food conversation step:**
- Primary code: add to `handlers/conversation/nonfood_*.py`, usually `nonfood_editing.py` for top-level routing or a focused sibling module for a child subflow.
- State: add `NONFOOD_*` enum member in `states.py` only when required.
- Wiring: update `handlers/conversation/nonfood_editing.py::nonfood_conv` or a nested non-food `ConversationHandler`.
- Tests: extend `tests/test_nonfood_conversation.py` and `tests/test_nonfood_contracts.py`.

**New Excel parsing/generation behavior:**
- Primary code: `services/excel_service.py`.
- Config constants: add fields to `services/excel_service.py::ExcelConfig` rather than scattering row/column literals in handlers.
- Tests: add workbook-focused tests in `tests/test_nonfood_excel_service.py` or a new `tests/test_excel_service.py`.

**New persistence operation:**
- Primary code: `data/mongodb_repository.py`.
- Public export: add it to `data/__init__.py::__all__` and import list.
- Tests: add repository tests under `tests/`, following `tests/test_nonfood_repository.py` patterns.

**New reusable model:**
- Primary code: `models/`.
- Pattern: use dataclasses with `from_dict()` and `to_dict()` methods like `models/order.py::OrderItem` and `models/food_item.py::FoodItem`.
- Tests: add conversion tests under `tests/` if handlers/services depend on the model.

**New inline keyboard helper:**
- Primary code: `keyboards/inline.py` for food helpers or a new explicitly named helper module if non-food callbacks are involved.
- Pattern: preserve callback namespaces exactly as handlers expect.
- Tests: cover callback data contracts when prefixes can collide.

## Deprecated Shims

**`db.py`:**
- Purpose: Backward-compatible import shim for MongoDB repository functions.
- Use instead: import from `data` or `data.mongodb_repository.py`.
- Rule: Do not add new persistence behavior to `db.py`; add it to `data/mongodb_repository.py` and export it through `data/__init__.py`.

**`r2.py`:**
- Purpose: Backward-compatible import shim for R2 storage functions.
- Use instead: import from `data` or `data.r2_storage.py`.
- Rule: Do not add new object-storage behavior to `r2.py`; add it to `data/r2_storage.py` and export it through `data/__init__.py` when needed.

## Special Directories

**`dashboard/`:**
- Purpose: Dashboard scaffold placeholder.
- Generated: Partially; observed contents are cache/scaffold artifacts.
- Committed: Directory presence exists, but active Python source files are not present in the observed tree.
- Use rule: Do not route runtime bot changes through `dashboard/`.

**`.planning/`:**
- Purpose: GSD project state, roadmap, research, debug, and codebase mapping artifacts.
- Generated: Yes.
- Committed: Project-dependent; do not modify except for GSD workflow outputs such as `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/STRUCTURE.md`.

**`__pycache__/` and `.pytest_cache/`:**
- Purpose: Python and pytest cache artifacts.
- Generated: Yes.
- Committed: Should not be used as source of truth.
- Use rule: Ignore when adding or moving application code.

**`.venv/`:**
- Purpose: Local virtual environment.
- Generated: Yes.
- Committed: Should not be edited by source changes.
- Use rule: Do not inspect or modify for application architecture work.

---

*Structure analysis: 2026-04-24*
