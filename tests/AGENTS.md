# TEST SUITE KNOWLEDGE BASE

**Generated:** 2026-04-22
**Parent:** `../AGENTS.md`

## OVERVIEW

Pytest regression layer for the bot. Strongest coverage is the non-food FSM, using fake Telegram modules and monkeypatched data/service seams instead of real integrations.

## STRUCTURE

```
tests/
├── test_nonfood_conversation.py    # End-to-end non-food handler flow with fake Telegram runtime
├── test_food_flow_regression.py    # Guardrails for callback/session-key separation
├── test_nonfood_bootstrap.py       # bot.py non-food bootstrap contract
├── test_nonfood_repository.py      # Mongo repository isolation for non-food collections
├── test_nonfood_excel_service.py   # Non-food Excel workbook generation
└── test_bot.py                     # Legacy utility expectations; partly stale
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Non-food FSM behavior | `test_nonfood_conversation.py` | Main regression anchor; 1200+ lines |
| Food vs non-food namespace safety | `test_food_flow_regression.py` | Callback prefix + session-key collision checks |
| Non-food bootstrap fallback | `test_nonfood_bootstrap.py` | R2 vs local workbook contract |
| Mongo isolation | `test_nonfood_repository.py` | Non-food collections must stay separate from food collections |
| Excel generation contract | `test_nonfood_excel_service.py` | Preserves formulas while writing code/qty |
| Legacy utility expectations | `test_bot.py` | Imports `fmt_qty` and `get_categories` from `bot.py`; currently out of sync |

## CONVENTIONS

- Prefer fake Telegram objects over importing the real Telegram runtime in unit-style tests.
- Use `monkeypatch` to replace `data.*` and bootstrap collaborators instead of live MongoDB/R2.
- Keep food/non-food namespace assertions explicit; callback-prefix collisions are regressions.
- Async handlers are exercised with `asyncio.run(...)`, not a dedicated async plugin.
- Preserve Vietnamese-facing strings in assertions when testing user-visible copy.

## SHARED TEST PATTERNS

- `_FakeMessage`, `_FakeCallbackQuery`, `_FakeContext`, and module injection via `sys.modules` simulate Telegram.
- `_import_*_module()` helpers load handler modules after stub installation to avoid Telegram import requirements.
- Repository tests use in-memory fake collection/cursor objects and inspect recorded calls.
- Bootstrap tests inject fake service classes to validate fallback order without real workbooks.
- Excel tests build minimal in-memory workbooks and assert only contractually important cells.

## HOTSPOTS

- `test_nonfood_conversation.py` is the biggest file in the repo and the strongest behavioral source of truth for non-food flows.
- `test_food_flow_regression.py` is small but high leverage: it protects callback namespaces, session-key boundaries, and bot wiring assumptions.
- `test_bot.py` is a legacy edge case: it still expects `fmt_qty` and `get_categories` exports from `bot.py`.

## ANTI-PATTERNS

- Do not add tests that import real Telegram classes when the existing stub pattern is sufficient.
- Do not blur food and non-food callback prefixes or session keys in fixtures.
- Do not rewrite large regression tests into tiny unit shards if that loses state-transition coverage.
- Do not assume `test_bot.py` reflects the latest architecture without checking production code first.
- Do not hit real MongoDB or R2 from this suite; keep tests deterministic and local.

## GOTCHAS

- `test_nonfood_conversation.py` installs fake `telegram` and `telegram.ext` modules before importing handlers.
- Several tests validate contracts indirectly by inspecting AST/source text rather than importing the full runtime.
- The suite is non-food heavy; food coverage is mostly regression guards rather than mirrored end-to-end flow tests.
- `pytest` is used in practice but is still missing from `requirements.txt`.
