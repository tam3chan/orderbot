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
    out_item_end: int = 40
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

        # 1. Xoá các dòng thừa (từ 19 đến 24)
        ws.delete_rows(19, 6)

        item_count = len(order_items)
        template_row = self._config.out_item_start # Dòng 18

        # 2. Insert rows và copy style/công thức từ dòng 18
        if item_count > 1:
            ws.insert_rows(template_row + 1, item_count - 1)
            
            from copy import copy
            from openpyxl.formula.translate import Translator
            
            for i in range(1, item_count):
                r = template_row + i
                for c in range(1, ws.max_column + 1):
                    src_cell = ws.cell(row=template_row, column=c)
                    dst_cell = ws.cell(row=r, column=c)
                    
                    if src_cell.has_style:
                        dst_cell.font = copy(src_cell.font)
                        dst_cell.border = copy(src_cell.border)
                        dst_cell.fill = copy(src_cell.fill)
                        dst_cell.number_format = src_cell.number_format
                        dst_cell.protection = copy(src_cell.protection)
                        dst_cell.alignment = copy(src_cell.alignment)
                    
                    if src_cell.data_type == 'f' and src_cell.value:
                        try:
                            dst_cell.value = Translator(src_cell.value, origin=src_cell.coordinate).translate_formula(dst_cell.coordinate)
                        except Exception as e:
                            logger.error(f"Formula translation error at {src_cell.coordinate}: {e}")
                            dst_cell.value = src_cell.value

        # 3. Đưa data vào các dòng
        for i, item in enumerate(order_items):
            r = template_row + i
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
