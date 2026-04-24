## 2026-04-21

- Prior attempt drifted into Excel workbook feature work; Task 1 is bootstrap/config only, so `services/excel_service.py` was restored and kept out of scope.
- Full `pytest tests -q` currently fails in stale `tests/test_bot.py` imports (`telegram` missing, old bot helpers no longer exist). Treat that suite as a pre-existing baseline issue to replace with targeted regressions in later tasks, not as a Task-1 regression.

## Bug Fixes (Final Wave)

- **Issue 1 (CRITICAL):** `_show_nonfood_edit_screen` emitted `nfe:edit:{code}` but `handle_nonfood_edit_menu` matched only `^nfei:` — item editing completely broken. Fixed: button callback changed to `nfei:edit:{code}`.

- **Issue 2:** Edit screen had no way to trigger code search (`nf:search`). Fixed: added "🔍 Tìm mã" button with `callback_data="nf:search"` between item buttons and the action row.

- **Issue 3:** `handle_nonfood_entry`, `handle_nonfood_history_entry`, and `receive_nonfood_history_date` all set `nonfood_order` then returned `NONFOOD_EDITING` without calling `_show_nonfood_edit_screen` — user never saw the updated edit screen. Fixed: each branch now calls `await _show_nonfood_edit_screen(update, ctx)` and returns its result. Import added locally inside each function to avoid circular import.

- **Issue 4 (R2 fallback):** R2 download and local instantiation were in one try/except. If `download_excel_fn` raised ANY exception (network, 404), bootstrap jumped to `except:` and disabled non-food entirely, never trying `NONFOOD_EXCEL_PATH`. Fixed: restructured to try R2 first, fall back to local path on exception, then fall back to disable on second exception. Added `logger.warning` when R2 fails so failures are visible without full stack trace.

- **Issue 5 (Excel formulas):** `build_order_excel_nonfood` did `ws.cell(..., value=None)` for ALL columns A-K in rows 16-26, destroying VLOOKUP formulas. Fixed: only clears columns B (code) and G (qty) before writing — formula columns C, E, H, K are left untouched.
