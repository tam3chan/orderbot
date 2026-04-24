# KEYBOARDS KNOWLEDGE BASE

**Generated:** 2026-04-24
**Parent:** `../AGENTS.md`

## OVERVIEW

Inline keyboard builders for Telegram bot screens. This directory owns callback payload strings for food flow helpers and must stay aligned with conversation handlers.

## STRUCTURE

```
keyboards/
├── inline.py   # Food inline keyboard builders and quantity formatter
└── __init__.py # Re-exports keyboard helpers
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Edit screen buttons | `edit_screen_kbd()` | Uses `ei:`, `add_item`, `done_editing`, `save_tpl_btn` |
| Category browsing | `category_kbd()` / `item_kbd()` | Uses `cat:` and `item:` payloads |
| Quantity edit keypad | `edit_item_kbd()` | Uses `eq:` payload family |
| Confirm/date buttons | `confirm_kbd()` / `date_kbd()` | Uses `confirm_*`, `change_date`, `qdate:` |
| History/template entry | `history_kbd()` / `entry_point_kbd()` / `template_menu_kbd()` | Uses `hi:` and `en:` payloads |
| Template save | `template_save_kbd()` | Uses `tpl_ow:`, `tpl_new`, `tpl_cancel` |

## CALLBACK CONTRACTS

- Food entry/history: `en:`, `hi:`.
- Food category/item: `cat:`, `item:`.
- Food edit quantity: `ei:`, `eq:`.
- Food confirm/date/template save: `confirm_*`, `qdate:`, `tpl_*`.
- Non-food callback families live mostly in `handlers/conversation/nonfood_*`; keep them disjoint from these food prefixes.

## CONVENTIONS

- Preserve Vietnamese button text and emoji style unless UX copy is explicitly in scope.
- Truncate long item labels before creating buttons; Telegram button labels should stay compact.
- Keep callback payloads parseable by the matching handler prefix checks.
- When changing a callback string, update handler filters and namespace regression tests together.

## ANTI-PATTERNS

- Do not introduce callback prefixes that collide with non-food (`nfe:`, `nfh:`, `nfei:`, `nfeq:`, `nf:`, `nfsearch:`, `nftpl:`).
- Do not import heavy bot startup code from keyboard builders.
- Do not hide database reads in new keyboard helpers unless the existing handler contract already expects it.
- Do not assume `fmt_qty` here is exported by `bot.py`; legacy tests may still make that stale assumption.

## TEST REFERENCES

- `../tests/test_food_flow_regression.py`: callback namespace separation guardrails.
- `../tests/test_nonfood_contracts.py`: non-food namespace must remain explicit and disjoint.
