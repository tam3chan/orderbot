# Research: Telegram ordering bot roadmap inputs

## Findings

- Use persistent conversation state or document volatility for Telegram restart recovery.
- Add central async error handling with traceback logging and optional admin alerts.
- Use MongoDB singleton clients with explicit timeouts and indexes for order history/templates.
- Treat MongoDB as canonical order storage; treat Excel as import/export format.
- Validate workbook sheets/columns before parsing.
- Use deterministic R2/S3 object keys, private storage, and retry-safe upload/download helpers.
- Improve Telegram UX with back/cancel/edit/resume paths and clear confirmation screens.
- If dashboard is revived, start with authenticated read-only operational views before write actions.

## Recommended roadmap themes

1. Reliability: persistence, timeouts, error handling, restart recovery.
2. Data integrity: schema/index review, duplicate protection, canonical DB records.
3. Excel hardening: schema validation, file-size limits, streaming paths.
4. Storage hardening: deterministic keys, private access, retry-safe uploads.
5. UX: drafts, resume, back/edit, clearer errors.
6. Observability: structured logs, admin alerts, health checks.
7. Dashboard: minimal authenticated operational console.

## Open questions

- Which deployment target is production: Railway only, Docker host, or other?
- Are generated Excel files shared directly in Telegram only, or should R2 links become user-facing?
