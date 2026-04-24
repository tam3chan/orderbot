## Telegram flow patterns

- `bot.py` is the wiring hub: top-level `/order` ConversationHandler plus shared command handlers (`/start`, `/list`, `/tim`, `/cancel`).
- Callback namespaces are prefix-based and isolated by flow: `en:` (entry), `hi:` (history), `ei:` (edit item), `eq:` (edit qty), `cat:` (category/item browse), `confirm_yes|no`, `qdate:` (date picker), `tpl_` (template save).
- `ctx.user_data` is the session store for the whole order: `order`, `order_date`, `editing_code`, `current_cat`, `current_item`, `tpl_action`.
- Nested flow pattern exists in `handlers/conversation/*` with local `ConversationHandler` objects for category/template/history/date selection.
- Package structure to mirror: `handlers/conversation/{entry,editing,category,history,confirm,template}.py` plus `states.py` and `keyboards/inline.py`.
