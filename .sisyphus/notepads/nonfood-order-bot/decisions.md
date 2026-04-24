## 2026-04-21

- Task 1 is limited to startup/bootstrap: food startup stays unchanged, non-food bootstrap is isolated behind `nonfood_enabled` and dedicated `bot_data` keys.
- Task 3 will keep non-food separate at the contract layer only: `OrderStates` gets a distinct non-food block, and the callback/session namespace is locked to `nfe:`, `nfh:`, `nfcat:`, `nfitem:`, `nfsearch:`, `nfei:`, `nfeq:`, `nftpl:`, `nfqdate:` plus the dedicated non-food session keys.
- Non-food persistence is isolated at the repository layer with dedicated `nonfood_orders` and `nonfood_templates` collections; no `type` field or shared food collection is used.
- The public `data` package exports the non-food repository APIs so later handlers can import them without reaching into `mongodb_repository` directly.
- Task 4 keeps the entry/history loader self-contained: `/order_nonfood` initializes `nonfood_order` and `nonfood_order_date`, routes only through `nfe:`/`nfh:` callbacks, and hands off by returning non-food states without pulling in unfinished browse/edit modules.
- Non-food `receive_qty` ends by calling a local `_show_nonfood_edit_screen` helper that returns `NONFOOD_EDITING`, rather than calling `show_edit_screen` from `editing.py` (which returns `EDITING`). This keeps the food editing module untouched and avoids importing it into non-food flow.
- Non-food category browse uses the same nested `ConversationHandler` pattern as food, with `nf:add_item` as entry point, `nfcat:` for category callbacks, and `nfitem:` for item callbacks. Back from items goes to cats (`NONFOOD_CHOOSING_CAT`); back from cats returns to `NONFOOD_EDITING` via `map_to_parent`.
