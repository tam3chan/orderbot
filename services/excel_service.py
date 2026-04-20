"""Excel loading and order file generation service."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import date

from openpyxl import load_workbook

logger = logging.getLogger(__name__)


@dataclass
class ExcelConfig:
    """Excel sheet and column configuration."""
    sheet_src: str = "Food T01"
    sheet_out: str = "PR NOODLE"
    # Source column indices (0-based from Excel)
    col_cat: int = 1
    col_sub: int = 2
    col_code: int = 3
    col_name: int = 4
    col_ncc: int = 9
    col_unit: int = 20
    # Output row/column positions
    out_date_row: int = 4
    out_date_col: int = 12
    out_item_start: int = 18
    out_stt: int = 1
    out_ma_sp: int = 2
    out_ten_hang: int = 3
    out_so_luong: int = 7
    out_dvt: int = 9
    out_ngay_giao: int = 10
    out_ncc: int = 15


class ExcelService:
    """Handles Excel loading and order file generation."""

    def __init__(self, buffer: io.BytesIO | None = None, local_path: str | None = None):
        self._buffer = buffer
        self._local_path = local_path
        self._config = ExcelConfig()
        self._items: dict | None = None
        self._categories: dict | None = None

    def load_items(self) -> tuple[dict, dict]:
        """Load and parse food items from Excel. Returns (items, categories)."""
        if self._items is not None:
            return self._items, self._categories

        wb = self._get_workbook(read_only=True, data_only=True)
        if self._config.sheet_src not in wb.sheetnames:
            raise ValueError(f"Sheet '{self._config.sheet_src}' not found")

        items = {}
        for row in wb[self._config.sheet_src].iter_rows(min_row=3, values_only=True):
            code, name = row[self._config.col_code], row[self._config.col_name]
            if code and name and str(name) != "TÊN SẢN PHẨM":
                items[str(code)] = {
                    "code": code,
                    "name": str(name),
                    "unit": str(row[self._config.col_unit]) if row[self._config.col_unit] else "kg",
                    "cat": str(row[self._config.col_cat]) if row[self._config.col_cat] else "Khác",
                    "sub": str(row[self._config.col_sub]) if row[self._config.col_sub] else "",
                    "ncc": str(row[self._config.col_ncc]) if row[self._config.col_ncc] else "",
                }
        wb.close()

        categories: dict = {}
        for v in items.values():
            categories.setdefault(v["cat"], []).append(v)

        self._items = items
        self._categories = categories
        logger.info("Loaded %d items", len(items))
        return items, categories

    def build_order_excel(self, order_items: list, order_date: date) -> io.BytesIO:
        """Generate order Excel file from list of order items."""
        wb = self._get_workbook()
        if self._config.sheet_out not in wb.sheetnames:
            raise ValueError(f"Sheet '{self._config.sheet_out}' not found")

        ws = wb[self._config.sheet_out]
        ws.cell(row=self._config.out_date_row, column=self._config.out_date_col, value=order_date)

        for i, item in enumerate(order_items):
            r = self._config.out_item_start + i
            ws.cell(row=r, column=self._config.out_stt, value=i + 1)
            ws.cell(row=r, column=self._config.out_ma_sp, value=item["code"])
            ws.cell(row=r, column=self._config.out_ten_hang, value=item["name"])
            ws.cell(row=r, column=self._config.out_so_luong, value=item["qty"])
            ws.cell(row=r, column=self._config.out_dvt, value=item["unit"])
            ws.cell(row=r, column=self._config.out_ngay_giao, value=order_date.strftime("%d/%m/%Y"))
            ws.cell(row=r, column=self._config.out_ncc, value=item["ncc"])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def _get_workbook(self, read_only: bool = False, data_only: bool = False):
        if self._buffer is not None:
            self._buffer.seek(0)
            return load_workbook(self._buffer, read_only=read_only, data_only=data_only)
        return load_workbook(self._local_path, read_only=read_only, data_only=data_only)
