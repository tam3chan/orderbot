"""Tests for non-food bootstrap contract."""
from __future__ import annotations

import io
import os
import sys
import types

os.environ.setdefault("BOT_TOKEN", "fake_token_for_testing")
os.environ.setdefault("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")


class _FakeWorkbook:
    def close(self) -> None:
        return None


class _RecordingService:
    instances: list["_RecordingService"] = []

    def __init__(self, buffer=None, local_path=None):
        self.buffer = buffer
        self.local_path = local_path
        type(self).instances.append(self)

    def load_items_nonfood(self):
        return (
            {
                "NF01": {"code": "NF01", "name": "Nonfood item", "cat": "KHAC", "unit": "cai", "source": "CCDC"}
            },
            {"KHAC": [{"code": "NF01", "name": "Nonfood item", "cat": "KHAC", "unit": "cai", "source": "CCDC"}]},
        )


class _BrokenService(_RecordingService):
    def load_items_nonfood(self):
        raise ValueError("broken workbook")


class _FilterToken:
    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

    def __invert__(self):
        return self


def _import_bot():
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

    sys.modules.pop("bot", None)
    return __import__("bot")


def test_bootstrap_nonfood_uses_r2_when_configured_and_populates_catalog(monkeypatch):
    bot = _import_bot()

    monkeypatch.setenv("R2_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("R2_ACCESS_KEY", "key")
    monkeypatch.setenv("R2_SECRET_KEY", "secret")
    monkeypatch.setenv("NONFOOD_R2_OBJECT_KEY", "NONFOOD_FROM_R2.xlsx")
    monkeypatch.setenv("NONFOOD_EXCEL_PATH", "ignored-local.xlsx")

    seen = {}

    def fake_download_excel(*, object_key=None):
        seen["object_key"] = object_key
        return io.BytesIO(b"dummy-nonfood-workbook")

    _RecordingService.instances.clear()
    assets = bot._bootstrap_nonfood_assets(
        service_cls=_RecordingService,
        download_excel_fn=fake_download_excel,
    )

    assert seen["object_key"] == "NONFOOD_FROM_R2.xlsx"
    assert _RecordingService.instances[-1].buffer is assets["nonfood_excel_buffer"]
    assert _RecordingService.instances[-1].local_path is None
    assert assets["nonfood_enabled"] is True
    assert assets["nonfood_items"]["NF01"]["name"] == "Nonfood item"
    assert assets["nonfood_categories"]["KHAC"][0]["code"] == "NF01"


def test_bootstrap_nonfood_falls_back_to_local_path_before_default(monkeypatch):
    bot = _import_bot()

    monkeypatch.delenv("R2_ENDPOINT", raising=False)
    monkeypatch.delenv("R2_ACCESS_KEY", raising=False)
    monkeypatch.delenv("R2_SECRET_KEY", raising=False)
    monkeypatch.setenv("NONFOOD_EXCEL_PATH", "custom-nonfood.xlsx")
    monkeypatch.delenv("NONFOOD_R2_OBJECT_KEY", raising=False)

    _RecordingService.instances.clear()
    assets = bot._bootstrap_nonfood_assets(service_cls=_RecordingService)

    assert _RecordingService.instances[-1].buffer is None
    assert _RecordingService.instances[-1].local_path == "custom-nonfood.xlsx"
    assert assets["nonfood_enabled"] is True
    assert assets["nonfood_items"]["NF01"]["code"] == "NF01"
    assert assets["nonfood_categories"]["KHAC"][0]["name"] == "Nonfood item"


def test_bootstrap_nonfood_uses_default_local_path_when_unset(monkeypatch):
    bot = _import_bot()

    monkeypatch.delenv("R2_ENDPOINT", raising=False)
    monkeypatch.delenv("R2_ACCESS_KEY", raising=False)
    monkeypatch.delenv("R2_SECRET_KEY", raising=False)
    monkeypatch.delenv("NONFOOD_EXCEL_PATH", raising=False)
    monkeypatch.delenv("NONFOOD_R2_OBJECT_KEY", raising=False)

    _RecordingService.instances.clear()
    assets = bot._bootstrap_nonfood_assets(service_cls=_RecordingService)

    assert _RecordingService.instances[-1].local_path == bot.NONFOOD_EXCEL_PATH
    assert assets["nonfood_enabled"] is True
    assert assets["nonfood_items"]["NF01"]["code"] == "NF01"
    assert assets["nonfood_categories"]["KHAC"][0]["source"] == "CCDC"


def test_bootstrap_nonfood_invalid_default_file_degrades_gracefully(monkeypatch):
    bot = _import_bot()

    monkeypatch.delenv("R2_ENDPOINT", raising=False)
    monkeypatch.delenv("R2_ACCESS_KEY", raising=False)
    monkeypatch.delenv("R2_SECRET_KEY", raising=False)
    monkeypatch.delenv("NONFOOD_EXCEL_PATH", raising=False)
    monkeypatch.delenv("NONFOOD_R2_OBJECT_KEY", raising=False)

    assets = bot._bootstrap_nonfood_assets(service_cls=_BrokenService)

    assert assets["nonfood_enabled"] is False
    assert assets["nonfood_items"] == {}
    assert assets["nonfood_categories"] == {}
    assert assets["nonfood_excel_service"] is None
    assert assets["nonfood_order_service"] is None
