# CONVERSATION FLOW KNOWLEDGE BASE

**Generated:** 2026-04-22
**Parent:** `../../AGENTS.md`

## OVERVIEW

FSM layer for Telegram ordering. This directory owns state transitions, callback namespaces, and the mirrored food/non-food conversation flows.

## STRUCTURE

```
handlers/conversation/
├── entry.py / nonfood_entry.py           # Flow entry + history menus
├── category.py / nonfood_category.py     # Browse category → item → qty
├── editing.py / nonfood_editing.py       # Central edit hub + nested wiring
├── confirm.py / nonfood_confirm.py       # Confirm, date choice, export
├── template.py / nonfood_template.py     # Save/load templates
├── history.py                            # Food history subflow
└── nonfood_search.py                     # Exact-code non-food search
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Food entry menu | `entry.py` | `/order`, history jump, template jump |
| Food edit hub | `editing.py` | Central food editing state |
| Food confirm/date flow | `confirm.py` | Includes nested `date_conv` |
| Non-food top-level wiring | `nonfood_editing.py` | Builds `nonfood_conv` and imports sibling handlers |
| Non-food browse flow | `nonfood_category.py` | Adds items and returns to edit hub |
| Non-food search flow | `nonfood_search.py` | Exact code search namespace |
| Non-food export flow | `nonfood_confirm.py` | Confirm, date selection, Excel export |
| Shared state ids | `../../states.py` | All state constants live there |

## STATE MAP

- Food states: `ENTRY_POINT` → `EDITING` / `EDITING_ITEM` / `ENTERING_EDIT_QTY` / `CHOOSING_CAT` / `CHOOSING_ITEM` / `ENTERING_QTY` / `CHOOSING_HISTORY` / `ENTERING_HISTORY_DATE` / `CONFIRM_ORDER` / `ENTERING_DATE` / `ENTERING_TEMPLATE_NAME`
- Non-food states: `NONFOOD_ENTRY_POINT` → `NONFOOD_EDITING` / `NONFOOD_EDITING_ITEM` / `NONFOOD_ENTERING_EDIT_QTY` / `NONFOOD_CHOOSING_CAT` / `NONFOOD_CHOOSING_ITEM` / `NONFOOD_ENTERING_QTY` / `NONFOOD_CHOOSING_HISTORY` / `NONFOOD_ENTERING_HISTORY_DATE` / `NONFOOD_CONFIRM_ORDER` / `NONFOOD_ENTERING_DATE` / `NONFOOD_ENTERING_TEMPLATE_NAME` / `NONFOOD_SEARCHING`
- Source of truth: `states.py` defines 25 enum members total. Do not hardcode stale 12-state assumptions.

## CALLBACK PREFIXES

- Food entry/history: `en:`, `hi:`
- Food category/items/add qty: `cat:`, `item:` plus text input for add-item quantity
- Food editing: `ei:`, `eq:`
- Food confirm/date: `confirm_*`, `qdate:`
- Non-food entry/history: `nfe:`, `nfh:`
- Non-food edit/item qty: `nfei:`, `nfeq:`
- Non-food browse/search/template: `nf:`, `nfsearch:`, `nftpl:`

Match new callback namespaces to the existing family. Prefix collisions between food and non-food flows are treated as regressions and are covered by tests.

## CONVENTIONS

- Keep user-facing copy in Vietnamese.
- Return `OrderStates.*` members, not raw ints.
- Use `ctx.user_data` / `ctx.bot_data` as the session boundary; non-food flow keeps its own dedicated keys.
- Mirror food and non-food behavior deliberately. When changing one flow, inspect the sibling module pair before deciding the change is one-sided.
- Reuse helper screens such as `show_edit_screen()` / `_show_nonfood_edit_screen()` instead of rebuilding keyboards inline.

## ANTI-PATTERNS

- Do not introduce cross-flow callback prefixes that blur food vs non-food namespaces.
- Do not bypass `states.py` by inventing ad hoc state numbers in handlers.
- Do not move late imports casually: some imports are intentionally deferred to break circular dependencies, especially around edit/confirm transitions.
- Do not clear unrelated `user_data` keys in non-food handlers; use the dedicated session key set.
- Do not add English-only UI strings unless the surrounding UX is also being localized.

## GOTCHAS

- `confirm.py` imports `show_edit_screen` inside `back_to_edit()` to avoid a circular import.
- `nonfood_editing.py` is the orchestration hub for non-food flow and intentionally gathers imports from multiple sibling modules with `# noqa: E402` comments.
- Nested `ConversationHandler`s are part of the design here; changing patterns often breaks parent/child state mapping.
- Regression coverage is strongest in `tests/test_nonfood_conversation.py` and `tests/test_food_flow_regression.py`.
