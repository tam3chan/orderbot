## Implementation choices to copy

- Keep the top-level bot wiring thin: handler logic lives in `handlers/conversation/*`, not `bot.py`.
- Use one shared `OrderStates` enum for all nested subflows.
- Prefer callback prefixes over ad hoc callback names for each subflow.
- Store per-conversation state in `ctx.user_data`, not globals.
