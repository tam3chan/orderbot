## Gotchas

- `history_conv` and `date_conv` are defined, but `bot.py` currently wires only `category_conv` and `template_conv`; history/date are handled directly through state callbacks.
- `ctx.user_data.clear()` is called in `/order`, `/start`, `/cancel`, and after final confirm/cancel, so any new flow must repopulate its keys immediately.
- Several handlers import sibling modules inside the function to avoid circular imports (`show_edit_screen`, `_show_entry_point_menu`, `show_confirm_screen`).
- `allow_reentry=True` is enabled on the main `/order` ConversationHandler, so a new flow should avoid state collisions with reentered conversations.
- The main ConversationHandler matches by regex prefix; adding a new parallel flow means choosing a unique prefix and state mapping, or it will intercept existing callbacks.
