"""Order orchestration service."""
from __future__ import annotations

import io
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.excel_service import ExcelService


class OrderService:
    """Orchestrates order operations combining DB and Excel generation."""

    def __init__(self, db, excel_service: "ExcelService"):
        self._db = db
        self._excel = excel_service

    def create_order(self, order_date: date, items: list) -> io.BytesIO:
        """Save order to DB and generate Excel file."""
        self._db.save_order(order_date, items)
        return self._excel.build_order_excel(items, order_date)

    def get_recent_order(self) -> tuple[date, list] | None:
        """Get most recent order date and items."""
        dates = self._db.get_recent_dates(1)
        if not dates:
            return None
        d = date.fromisoformat(dates[0])
        items = self._db.get_order(d) or []
        return d, items

    def get_order_by_date(self, order_date: date) -> list | None:
        return self._db.get_order(order_date)

    def get_order_by_iso(self, iso_str: str) -> list | None:
        return self._db.get_order_by_iso(iso_str)

    def list_templates(self) -> list:
        return self._db.list_templates()

    def get_template(self, name: str) -> list | None:
        return self._db.get_template(name)

    def save_template(self, name: str, items: list) -> None:
        self._db.save_template(name, items)
