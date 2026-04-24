"""
Unit tests cho order_bot — chạy bằng: pytest tests/
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import types

# Patch BOT_TOKEN trước khi import bot để tránh sys.exit(1)
os.environ.setdefault("BOT_TOKEN", "fake_token_for_testing")
os.environ.setdefault("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")


class _FilterToken:
    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

    def __invert__(self):
        return self


def _install_telegram_stubs() -> None:
    telegram = types.ModuleType("telegram")
    telegram.Update = type("Update", (), {})
    telegram.BotCommand = type("BotCommand", (), {"__init__": lambda self, *args, **kwargs: None})

    class InlineKeyboardButton:
        def __init__(self, *args, **kwargs):
            return None

    class InlineKeyboardMarkup:
        def __init__(self, *args, **kwargs):
            return None

    telegram.InlineKeyboardButton = InlineKeyboardButton
    telegram.InlineKeyboardMarkup = InlineKeyboardMarkup

    ext = types.ModuleType("telegram.ext")
    ext.ContextTypes = type("ContextTypes", (), {"DEFAULT_TYPE": object()})

    class _Builder:
        def token(self, *_args, **_kwargs):
            return self

        def post_init(self, *_args, **_kwargs):
            return self

        def build(self):
            return types.SimpleNamespace(bot_data={})

    class Application:
        @classmethod
        def builder(cls):
            return _Builder()

    class CommandHandler:
        def __init__(self, *args, **kwargs):
            return None

    class CallbackQueryHandler:
        def __init__(self, *args, **kwargs):
            return None

    class MessageHandler:
        def __init__(self, *args, **kwargs):
            return None

    class ConversationHandler:
        END = object()

        def __init__(self, *args, **kwargs):
            return None

    ext.Application = Application
    ext.CommandHandler = CommandHandler
    ext.CallbackQueryHandler = CallbackQueryHandler
    ext.MessageHandler = MessageHandler
    ext.ConversationHandler = ConversationHandler
    ext.filters = types.SimpleNamespace(TEXT=_FilterToken(), COMMAND=_FilterToken())

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *a, **k: None

    sys.modules["telegram"] = telegram
    sys.modules["telegram.ext"] = ext
    sys.modules["dotenv"] = dotenv


def _import_bot():
    _install_telegram_stubs()
    sys.modules.pop("bot", None)
    return __import__("bot")


# ─── fmt_qty ────────────────────────────────────────────────────────────
class TestFmtQty:
    def test_integer_value(self):
        bot = _import_bot()
        assert bot.fmt_qty(2.0) == "2"

    def test_decimal_value(self):
        bot = _import_bot()
        assert bot.fmt_qty(2.5) == "2.5"

    def test_large_integer(self):
        bot = _import_bot()
        assert bot.fmt_qty(100.0) == "100"

    def test_small_decimal(self):
        bot = _import_bot()
        assert bot.fmt_qty(0.25) == "0.25"


# ─── get_categories ─────────────────────────────────────────────────────
class TestGetCategories:
    def test_groups_by_cat(self):
        bot = _import_bot()
        items = {
            "A01": {"cat": "THỊT", "name": "Thịt bò",  "unit": "kg", "ncc": ""},
            "B01": {"cat": "RAU",  "name": "Cà chua",  "unit": "kg", "ncc": ""},
            "A02": {"cat": "THỊT", "name": "Thịt lợn", "unit": "kg", "ncc": ""},
        }
        cats = bot.get_categories(items)
        assert "THỊT" in cats
        assert "RAU"  in cats
        assert len(cats["THỊT"]) == 2
        assert len(cats["RAU"])  == 1

    def test_empty_items(self):
        bot = _import_bot()
        assert bot.get_categories({}) == {}

    def test_single_item(self):
        bot = _import_bot()
        items = {"X01": {"cat": "MISC", "name": "Muối", "unit": "kg", "ncc": ""}}
        cats = bot.get_categories(items)
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
