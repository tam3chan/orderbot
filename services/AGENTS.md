# SERVICES KNOWLEDGE BASE

**Generated:** 2026-04-24
**Parent:** `../AGENTS.md`

## OVERVIEW

Business/service layer for Excel catalog parsing, workbook generation, and thin order orchestration. Handlers should call services for workbook logic instead of editing Excel directly.

## STRUCTURE

```
services/
├── excel_service.py # Food/non-food catalog loaders and workbook writers
├── order_service.py # Thin food order facade over db + ExcelService
└── __init__.py      # Service exports
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Food catalog parsing | `ExcelService.load_items()` | Reads `Food T01`, returns items + categories |
| Food workbook output | `ExcelService.build_order_excel()` | Writes formatted food order workbook |
| Non-food catalog parsing | `ExcelService.load_items_nonfood()` | Scans current `CCDC` and `VTTH` non-food sheets |
| Non-food workbook output | `ExcelService.build_order_excel_nonfood()` | Writes code/qty cells; preserves formulas |
| Sheet/cell constants | `ExcelConfig` | Update tests when changing workbook layout |
| Food orchestration wrapper | `OrderService` | Persists then builds food workbook |

## CONVENTIONS

- `ExcelService` accepts either an in-memory workbook buffer or a local path; preserve both startup modes.
- Food output fills detailed item rows; non-food output writes compact code/quantity rows into configured columns.
- Keep formula preservation behavior in workbook generation; tests assert important formula cells survive.
- Keep category dictionaries grouped by catalog category names; handlers depend on browsing shape.
- Raise/log workbook issues at service boundary; handlers own user-facing recovery text.

## ANTI-PATTERNS

- Do not duplicate Excel cell-writing logic in handlers.
- Do not hardcode workbook paths in services when constructor/env bootstrap already supplies them.
- Do not move Mongo collection decisions into `excel_service.py`; persistence belongs to `data/` or `OrderService`.
- Do not make non-food layout mirror food layout blindly; it has separate sheet/range/column config.
- Do not break in-memory workbook tests by requiring files on disk.

## TEST REFERENCES

- `../tests/test_nonfood_excel_service.py`: minimal workbook fixtures and formula-preservation checks.
- `../tests/test_nonfood_bootstrap.py`: bootstrap chooses R2 buffer vs local path before constructing service.
