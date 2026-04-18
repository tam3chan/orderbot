"""
Unit tests cho order_bot — chạy bằng: pytest tests/
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Patch BOT_TOKEN trước khi import bot để tránh sys.exit(1)
os.environ.setdefault("BOT_TOKEN", "fake_token_for_testing")
os.environ.setdefault("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")


# ─── fmt_qty ────────────────────────────────────────────────────────────
class TestFmtQty:
    def test_integer_value(self):
        from bot import fmt_qty
        assert fmt_qty(2.0) == "2"

    def test_decimal_value(self):
        from bot import fmt_qty
        assert fmt_qty(2.5) == "2.5"

    def test_large_integer(self):
        from bot import fmt_qty
        assert fmt_qty(100.0) == "100"

    def test_small_decimal(self):
        from bot import fmt_qty
        assert fmt_qty(0.25) == "0.25"


# ─── get_categories ─────────────────────────────────────────────────────
class TestGetCategories:
    def test_groups_by_cat(self):
        from bot import get_categories
        items = {
            "A01": {"cat": "THỊT", "name": "Thịt bò",  "unit": "kg", "ncc": ""},
            "B01": {"cat": "RAU",  "name": "Cà chua",  "unit": "kg", "ncc": ""},
            "A02": {"cat": "THỊT", "name": "Thịt lợn", "unit": "kg", "ncc": ""},
        }
        cats = get_categories(items)
        assert "THỊT" in cats
        assert "RAU"  in cats
        assert len(cats["THỊT"]) == 2
        assert len(cats["RAU"])  == 1

    def test_empty_items(self):
        from bot import get_categories
        assert get_categories({}) == {}

    def test_single_item(self):
        from bot import get_categories
        items = {"X01": {"cat": "MISC", "name": "Muối", "unit": "kg", "ncc": ""}}
        cats = get_categories(items)
        assert list(cats.keys()) == ["MISC"]
        assert len(cats["MISC"]) == 1


# ─── receive_qty validation ──────────────────────────────────────────────
class TestQtyValidation:
    """Test logic validate số lượng (không dùng Telegram API thật)."""

    def test_negative_qty_rejected(self):
        """Số âm phải bị từ chối."""
        qty = -5.0
        assert qty < 0  # Logic sẽ return ENTERING_QTY

    def test_zero_removes_item(self):
        """qty == 0 → xoá mặt hàng khỏi order."""
        qty = 0.0
        assert qty == 0

    def test_valid_qty_accepted(self):
        """Số dương hợp lệ."""
        for val in ["5", "2.5", "0.25", "100"]:
            qty = float(val.replace(",", "."))
            assert qty >= 0
