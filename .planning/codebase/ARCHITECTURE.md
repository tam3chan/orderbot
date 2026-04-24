# Architecture

**Analysis Date:** 2026-04-24

## Pattern Overview

**Overall:** Async `python-telegram-bot` application with explicit finite-state conversation handlers, Excel workbook business services, and function-based MongoDB/R2 adapters.

**Key Characteristics:**
- `bot.py` is the composition root: loads environment variables, bootstraps food/non-food Excel catalogs, builds `telegram.ext.Application`, stores shared dependencies in `app.bot_data`, and registers handlers.
- `states.py` is the state source of truth with 25 `OrderStates` enum members covering mirrored food and non-food flows.
- `handlers/conversation/` owns the FSM, callback namespaces, nested `ConversationHandler`s, and `ctx.user_data` session payloads.
- `services/excel_service.py` owns workbook parsing and output workbook generation for both food and non-food orders.
- `data/mongodb_repository.py` and `data/r2_storage.py` are persistence/storage adapters exposed through `data/__init__.py`.

## Layers

**Application Bootstrap:**
- Purpose: Start the bot, load assets, register commands, and wire handlers.
- Location: `bot.py`
- Contains: `main()`, `_init_excel_buffer()`, `_bootstrap_nonfood_assets()`, `_build_bot_data()`, `post_init()`, `authorized_only()`.
- Depends on: `states.py`, `services/excel_service.py`, `services/order_service.py`, `data/__init__.py`, `data/r2_storage.py`, `handlers/`.
- Used by: Python process entry via `if __name__ == "__main__": main()`.

**State Registry:**
- Purpose: Provide stable enum keys for parent and nested conversation states.
- Location: `states.py`
- Contains: food states `ENTRY_POINT` through `ENTERING_TEMPLATE_NAME`, plus non-food states `NONFOOD_ENTRY_POINT` through `NONFOOD_SEARCHING`.
- Depends on: Python `enum.Enum` only.
- Used by: `bot.py` and all modules under `handlers/conversation/`.

**Command Handlers:**
- Purpose: Handle top-level Telegram commands outside the order FSM.
- Location: `handlers/`
- Contains: `handlers/start.py`, `handlers/list.py`, `handlers/search.py`, `handlers/cancel.py`.
- Depends on: Telegram `Update`, `ContextTypes`, and shared catalog/persistence data in `ctx.bot_data` or `data`.
- Used by: `CommandHandler("start")`, `CommandHandler("list")`, `CommandHandler("tim")`, and `CommandHandler("cancel")` in `bot.py`.

**Food Conversation FSM:**
- Purpose: Build, edit, confirm, export, save, and template food orders.
- Location: `handlers/conversation/`
- Contains: `entry.py`, `editing.py`, `category.py`, `confirm.py`, `template.py`, `history.py`.
- Depends on: `states.py`, `data/__init__.py`, `services/excel_service.py`, Telegram inline keyboards.
- Used by: parent `ConversationHandler` declared in `bot.py` for `/order`.

**Non-Food Conversation FSM:**
- Purpose: Mirror the food workflow with separate state names, callback prefixes, session keys, exact-code search, and non-food workbook rules.
- Location: `handlers/conversation/`
- Contains: `nonfood_entry.py`, `nonfood_editing.py`, `nonfood_category.py`, `nonfood_search.py`, `nonfood_confirm.py`, `nonfood_template.py`.
- Depends on: `states.py`, `data/__init__.py`, `services/excel_service.py`, non-food assets in `ctx.bot_data`.
- Used by: `CommandHandler("order_nonfood", cmd_order_nonfood)` and `nonfood_conv` in `bot.py`.

**Services:**
- Purpose: Encapsulate business operations outside Telegram handler routing.
- Location: `services/`
- Contains: `services/excel_service.py`, `services/order_service.py`.
- Depends on: `openpyxl`, `dataclasses`, `datetime`, and `data` repository functions.
- Used by: `bot.py`, `handlers/conversation/confirm.py`, `handlers/conversation/nonfood_confirm.py`.

**Data and Storage:**
- Purpose: Persist orders/templates and fetch workbook templates.
- Location: `data/`
- Contains: `data/mongodb_repository.py`, `data/r2_storage.py`, `data/__init__.py`.
- Depends on: `pymongo`, `boto3`, environment variables.
- Used by: `bot.py`, entry/history/template/confirm handlers, and `services/order_service.py`.

**Models:**
- Purpose: Dataclass conversion helpers for order and catalog items.
- Location: `models/`
- Contains: `models/order.py`, `models/food_item.py`.
- Depends on: `dataclasses`, `datetime.date`.
- Used by: Available typed helpers; active handlers mostly pass dictionaries through `ctx.user_data` and MongoDB documents.

**Keyboard Builders:**
- Purpose: Inline keyboard helper functions for food UI.
- Location: `keyboards/inline.py`
- Contains: `edit_screen_kbd()`, `category_kbd()`, `item_kbd()`, `edit_item_kbd()`, `history_kbd()`, `date_kbd()`, `entry_point_kbd()`, `template_menu_kbd()`.
- Depends on: `telegram.InlineKeyboardButton`, `telegram.InlineKeyboardMarkup`.
- Used by: Existing handlers duplicate several keyboards inline; use helpers only when callback prefixes match current handlers exactly.

## Data Flow

**Food order flow:**
1. `/order` enters `handlers/conversation/entry.py::cmd_order()` and initializes `ctx.user_data["order"]` plus `ctx.user_data["order_date"]`.
2. Entry callbacks `en:*` in `handle_entry()` start a blank order, copy recent order data from `data.get_recent_dates()` / `data.get_order()`, load templates via `data.get_template()`, or enter history selection.
3. `handlers/conversation/editing.py::show_edit_screen()` renders `ctx.user_data["order"]` and routes `ei:*`, `eq:*`, `add_item`, `done_editing`, and `save_tpl_btn` actions.
4. Nested `handlers/conversation/category.py::category_conv` reads catalog data from `ctx.bot_data["categories"]` and `ctx.bot_data["items"]` and writes selected rows into `ctx.user_data["order"]`.
5. `handlers/conversation/confirm.py::confirm_yes()` builds an Excel file through `ctx.bot_data["excel_service"].build_order_excel()`, saves MongoDB state through `data.save_order()`, sends the document, and clears `ctx.user_data`.

**Non-food order flow:**
1. `/order_nonfood` is exposed in `bot.py` and implemented in `handlers/conversation/nonfood_entry.py::cmd_order_nonfood()`.
2. Session data uses dedicated keys such as `ctx.user_data["nonfood_order"]`, `ctx.user_data["nonfood_order_date"]`, `nf_current_item`, and `nf_editing_code`.
3. `handlers/conversation/nonfood_editing.py::nonfood_conv` routes non-food edit, category, search, template, confirm, and date states.
4. `handlers/conversation/nonfood_category.py` reads `ctx.bot_data["nonfood_categories"]` and `ctx.bot_data["nonfood_items"]`; items include a `source` badge from `CCDC` or `VTTH`.
5. `handlers/conversation/nonfood_confirm.py::_do_nonfood_export()` uses `ctx.bot_data["nonfood_excel_service"].build_order_excel_nonfood()`, persists via `data.save_nonfood_order()`, sends the workbook, then removes `NONFOOD_SESSION_KEYS`.

**Workbook bootstrap flow:**
1. `bot.py::_init_excel_buffer()` downloads the food workbook from R2 through `data.r2_storage.download_excel()` when R2 env vars exist; otherwise it uses local `EXCEL_PATH`.
2. `bot.py::main()` creates `ExcelService(buffer=EXCEL_BUFFER, local_path=EXCEL_PATH)` and calls `load_items()`.
3. `bot.py::_bootstrap_nonfood_assets()` attempts R2 download when non-food R2 configuration exists, then falls back to `NONFOOD_EXCEL_PATH` or `ORDER NONFOOD MIN xlsx.xlsx`.
4. Loaded assets are stored in `app.bot_data` under food keys (`excel_service`, `items`, `categories`) and non-food keys (`nonfood_enabled`, `nonfood_excel_service`, `nonfood_items`, `nonfood_categories`, `nonfood_order_service`).

**State Management:**
- Use `ctx.bot_data` for process-wide dependencies and catalogs created in `bot.py`.
- Use `ctx.user_data` for per-user in-progress order state.
- Food handlers may clear all `ctx.user_data` at completion/cancel; non-food handlers remove only `NONFOOD_SESSION_KEYS`.

## Key Abstractions

**`OrderStates`:**
- Purpose: Source of truth for Telegram conversation states.
- Examples: `states.py`, `bot.py`, `handlers/conversation/category.py`, `handlers/conversation/nonfood_editing.py`.
- Pattern: Return `OrderStates.*` members, not raw integers.

**Parent `ConversationHandler` for food:**
- Purpose: Own `/order` lifecycle and compose nested handlers.
- Examples: `bot.py` wiring for `OrderStates.ENTRY_POINT`, `OrderStates.EDITING`, `OrderStates.CONFIRM_ORDER`, and text input states.
- Pattern: Parent states include nested `category_conv` and `template_conv` inside `OrderStates.EDITING`.

**Nested `ConversationHandler`s:**
- Purpose: Isolate category/template/search/date subflows and map completion back to the parent hub.
- Examples: `handlers/conversation/category.py::category_conv`, `handlers/conversation/confirm.py::date_conv`, `handlers/conversation/nonfood_category.py::nonfood_category_conv`, `handlers/conversation/nonfood_search.py::nonfood_search_conv`.
- Pattern: Use `map_to_parent={ConversationHandler.END: OrderStates.EDITING}` or non-food equivalent for child completion.

**`ExcelService`:**
- Purpose: Read workbook catalogs and generate output workbooks.
- Examples: `services/excel_service.py::load_items()`, `load_items_nonfood()`, `build_order_excel()`, `build_order_excel_nonfood()`.
- Pattern: Keep workbook layout constants in `ExcelConfig`; access workbooks through `_get_workbook()` for buffer/local consistency.

**Function repository API:**
- Purpose: Provide simple persistence functions without repository objects in handlers.
- Examples: `data/mongodb_repository.py::save_order()`, `get_recent_dates()`, `save_nonfood_order()`, `list_nonfood_templates()`.
- Pattern: Import from `data` package root in handlers, e.g. `from data import save_order`.

## Entry Points

**Bot process:**
- Location: `bot.py::main()`
- Triggers: `python bot.py` and Docker container startup.
- Responsibilities: load Excel assets, build app, update `bot_data`, add handlers, run polling.

**Food ordering:**
- Location: `handlers/conversation/entry.py::cmd_order()`
- Triggers: Telegram `/order` command.
- Responsibilities: initialize food session, present recent/template/history/new-order choices.

**Non-food ordering:**
- Location: `handlers/conversation/nonfood_entry.py::cmd_order_nonfood()` and `handlers/conversation/nonfood_editing.py::nonfood_conv`
- Triggers: Telegram `/order_nonfood` command and `nfe:*` callback re-entry.
- Responsibilities: initialize non-food session and route non-food editing/confirm/search/template states.

**Catalog/list/search commands:**
- Location: `handlers/list.py`, `handlers/search.py`, `handlers/start.py`, `handlers/cancel.py`
- Triggers: `/list`, `/tim`, `/start`, `/cancel`.
- Responsibilities: utility bot interactions outside the main order builder.

## Error Handling

**Strategy:** Local validation in handlers plus broad exception handling around external IO and workbook generation.

**Patterns:**
- Validate quantities with `float(raw)` and return the same input state on `ValueError` in `handlers/conversation/category.py`, `editing.py`, `nonfood_category.py`, and `nonfood_editing.py`.
- Validate dates by parsing `DD/MM/YYYY` and returning date-entry states on failure in `handlers/conversation/entry.py`, `confirm.py`, `nonfood_entry.py`, and `nonfood_confirm.py`.
- Wrap Excel export in `try/except` in `handlers/conversation/confirm.py::confirm_yes()` and `handlers/conversation/nonfood_confirm.py::_do_nonfood_export()`.
- Disable non-food flow assets safely when `bot.py::_bootstrap_nonfood_assets()` cannot load a workbook.

## Cross-Cutting Concerns

**Logging:** Module-level loggers appear in `bot.py`, `services/excel_service.py`, and `data/r2_storage.py`; export failures use `logging.exception()` in confirm handlers.

**Validation:** Handlers validate quantities, dates, missing catalog items, empty orders, and missing workbook services at use sites.

**Authentication:** `bot.py` parses `ALLOWED_USER_IDS` and defines `authorized_only()`, but current handler registration uses raw handlers; wrap handlers before registration if access control is required.

**Persistence:** `data/mongodb_repository.py` uses a singleton `MongoClient`, database `orderbot`, unique date indexes for `orders` and `nonfood_orders`, and separate food/non-food template collections.

**Storage:** `data/r2_storage.py` downloads workbook templates into `io.BytesIO`; `ExcelService` accepts either buffer or local path.

**Dashboard Scaffold:** `dashboard/` contains scaffold/cache artifacts only in the observed tree; no active dashboard Python source files are present. Treat `dashboard/` as non-runtime until source files are restored.

---

*Architecture analysis: 2026-04-24*
