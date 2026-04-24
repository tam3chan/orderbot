"""Handler-flow tests for the non-food entry/history conversation."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import types
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data
from states import OrderStates


class _FakeInlineKeyboardButton:
    def __init__(self, text: str = "", callback_data: str | None = None, **kwargs):
        self.text = text
        self.callback_data = callback_data


class _FakeInlineKeyboardMarkup:
    def __init__(self, inline_keyboard: list[list[_FakeInlineKeyboardButton]]):
        self.inline_keyboard = inline_keyboard


class _FakeMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.reply_calls: list[dict[str, Any]] = []
        self.edit_calls: list[dict[str, Any]] = []

    async def reply_text(self, text: str, reply_markup: Any = None, parse_mode: str | None = None):
        self.reply_calls.append(
            {"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode}
        )

    async def edit_text(self, text: str, reply_markup: Any = None, parse_mode: str | None = None):
        self.edit_calls.append(
            {"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode}
        )


class _FakeCallbackQuery:
    def __init__(self, data: str, message: _FakeMessage):
        self.data = data
        self.message = message
        self.answer_calls: list[dict[str, Any]] = []

    async def answer(self, text: str | None = None, show_alert: bool = False):
        self.answer_calls.append({"text": text, "show_alert": show_alert})


class _FakeUpdate:
    def __init__(self, message: _FakeMessage | None = None, callback_query: _FakeCallbackQuery | None = None):
        self.message = message
        self.callback_query = callback_query


class _FakeContext:
    def __init__(self, user_data: dict[str, Any] | None = None, bot_data: dict[str, Any] | None = None):
        self.user_data: dict[str, Any] = user_data or {}
        self.bot_data: dict[str, Any] = bot_data or {}


def _install_telegram_stubs() -> None:
    telegram = types.ModuleType("telegram")
    setattr(telegram, "Update", type("Update", (), {}))
    setattr(telegram, "InlineKeyboardButton", _FakeInlineKeyboardButton)
    setattr(telegram, "InlineKeyboardMarkup", _FakeInlineKeyboardMarkup)

    # InputFile stub (accepts buffer + optional filename)
    class _FakeInputFile:
        def __init__(self, *a, **k):
            self._buffer = a[0] if a else k.get("buffer")
            self._filename = k.get("filename", "")

    setattr(telegram, "InputFile", _FakeInputFile)

    # Stub filters — filters.TEXT & ~filters.COMMAND just needs to be truthy
    class _FakeFilter:
        def __and__(self, other):
            return self
        def __invert__(self):
            return self

    fake_filters = types.ModuleType("telegram.ext.filters")
    setattr(fake_filters, "TEXT", _FakeFilter())
    setattr(fake_filters, "COMMAND", _FakeFilter())

    # Handler stubs that accept any args/kwargs without error
    def _make_handler_cls(name):
        class _H:
            def __init__(self, *a, **k):
                pass
        _H.__name__ = name
        return _H

    class _FakeConversationHandler:
        END = object()
        def __init__(self, *a, **k):
            pass

    ext = types.ModuleType("telegram.ext")
    setattr(ext, "ContextTypes", type("ContextTypes", (), {"DEFAULT_TYPE": object()}))
    setattr(ext, "ConversationHandler", _FakeConversationHandler)
    setattr(ext, "CallbackQueryHandler", _make_handler_cls("CallbackQueryHandler"))
    setattr(ext, "MessageHandler", _make_handler_cls("MessageHandler"))
    setattr(ext, "CommandHandler", _make_handler_cls("CommandHandler"))
    setattr(ext, "filters", fake_filters)

    sys.modules["telegram"] = telegram
    sys.modules["telegram.ext"] = ext


def _import_nonfood_entry_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_entry_module"
    module_path = Path(__file__).resolve().parents[1] / "handlers" / "conversation" / "nonfood_entry.py"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _callback_data(markup: _FakeInlineKeyboardMarkup) -> list[str]:
    return [
        str(button.callback_data)
        for row in markup.inline_keyboard
        for button in row
    ]


def _button_texts(markup: _FakeInlineKeyboardMarkup) -> list[str]:
    return [button.text for row in markup.inline_keyboard for button in row]


def _order_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["code"]): item for item in items}


RECENT_ITEMS = [
    {"code": "NF01", "name": "Giấy A4", "qty": 2, "unit": "ram"},
    {"code": "NF02", "name": "Bút bi", "qty": 5, "unit": "cây"},
]
HISTORY_ITEMS = [
    {"code": "NF03", "name": "Kẹp giấy", "qty": 3, "unit": "hộp"},
]
TEMPLATE_ITEMS = [
    {"code": "NF09", "name": "Khăn giấy", "qty": 4, "unit": "bịch"},
]


def test_entry_menu_branches(monkeypatch):
    module = _import_nonfood_entry_module()

    templates = [
        {"_id": "tpl-van-phong", "name": "Văn phòng"},
        {"_id": "tpl-ve-sinh", "name": "Vệ sinh"},
    ]
    recent_dates = ["2026-04-21", "2026-04-19"]
    items_by_iso = {
        "2026-04-21": RECENT_ITEMS,
        "2026-04-19": HISTORY_ITEMS,
    }
    templates_by_id = {
        "tpl-van-phong": TEMPLATE_ITEMS,
        "tpl-ve-sinh": RECENT_ITEMS,
    }

    monkeypatch.setattr(data, "get_recent_nonfood_dates", lambda n=7: recent_dates[:n])
    monkeypatch.setattr(
        data,
        "get_nonfood_order",
        lambda order_date: items_by_iso.get(order_date.isoformat()),
    )
    monkeypatch.setattr(
        data,
        "get_nonfood_order_by_iso",
        lambda iso_date: items_by_iso.get(iso_date),
    )
    monkeypatch.setattr(data, "list_nonfood_templates", lambda: templates)
    monkeypatch.setattr(
        data,
        "get_nonfood_template",
        lambda template_id: templates_by_id.get(template_id),
    )

    ctx = _FakeContext(
        user_data={
            "order": {"F01": {"code": "F01", "name": "Food", "qty": 1, "unit": "kg"}},
            "order_date": date(2026, 4, 20),
            "nonfood_order": {"OLD": {"code": "OLD"}},
            "nf_current_cat": "STALE",
            "other_key": "keep-me",
        },
        bot_data={"nonfood_enabled": True},
    )

    entry_message = _FakeMessage()
    start_state = asyncio.run(module.cmd_order_nonfood(_FakeUpdate(message=entry_message), ctx))

    assert start_state == OrderStates.NONFOOD_ENTRY_POINT
    assert ctx.user_data["order"]["F01"]["name"] == "Food"
    assert ctx.user_data["order_date"] == date(2026, 4, 20)
    assert ctx.user_data["other_key"] == "keep-me"
    assert ctx.user_data["nonfood_order"] == {}
    assert ctx.user_data["nonfood_order_date"] == date.today()
    assert "nf_current_cat" not in ctx.user_data

    entry_reply = entry_message.reply_calls[-1]
    assert entry_reply["text"] == "🧾 *Bắt đầu đơn non-food từ đâu?*"
    assert _callback_data(entry_reply["reply_markup"]) == [
        "nfe:recent",
        "nfe:tmpls",
        "nfe:hist",
        "nfe:new",
    ]

    recent_message = _FakeMessage()
    recent_query = _FakeCallbackQuery("nfe:recent", recent_message)
    recent_state = asyncio.run(
        module.handle_nonfood_entry(_FakeUpdate(callback_query=recent_query), ctx)
    )

    assert recent_state == OrderStates.NONFOOD_EDITING
    assert recent_query.answer_calls == [{"text": None, "show_alert": False}]
    assert ctx.user_data["nonfood_order"] == _order_map(RECENT_ITEMS)
    assert "order" in ctx.user_data
    assert "order_date" in ctx.user_data

    ctx.user_data["nonfood_order"] = {"STALE": {"code": "STALE"}}
    new_message = _FakeMessage()
    new_state = asyncio.run(
        module.handle_nonfood_entry(
            _FakeUpdate(callback_query=_FakeCallbackQuery("nfe:new", new_message)),
            ctx,
        )
    )
    assert new_state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"] == {}

    templates_message = _FakeMessage()
    templates_query = _FakeCallbackQuery("nfe:tmpls", templates_message)
    templates_state = asyncio.run(
        module.handle_nonfood_entry(_FakeUpdate(callback_query=templates_query), ctx)
    )

    assert templates_state == OrderStates.NONFOOD_ENTRY_POINT
    templates_markup = templates_message.edit_calls[-1]["reply_markup"]
    assert _callback_data(templates_markup) == [
        "nfe:tpl:tpl-van-phong",
        "nfe:tpl:tpl-ve-sinh",
        "nfe:back_main",
    ]

    template_pick_message = _FakeMessage()
    template_state = asyncio.run(
        module.handle_nonfood_entry(
            _FakeUpdate(
                callback_query=_FakeCallbackQuery("nfe:tpl:tpl-van-phong", template_pick_message)
            ),
            ctx,
        )
    )

    assert template_state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"] == _order_map(TEMPLATE_ITEMS)

    back_main_message = _FakeMessage()
    back_main_state = asyncio.run(
        module.handle_nonfood_entry(
            _FakeUpdate(callback_query=_FakeCallbackQuery("nfe:back_main", back_main_message)),
            ctx,
        )
    )
    assert back_main_state == OrderStates.NONFOOD_ENTRY_POINT
    assert _callback_data(back_main_message.edit_calls[-1]["reply_markup"]) == [
        "nfe:recent",
        "nfe:tmpls",
        "nfe:hist",
        "nfe:new",
    ]

    history_message = _FakeMessage()
    history_query = _FakeCallbackQuery("nfe:hist", history_message)
    history_state = asyncio.run(
        module.handle_nonfood_entry(_FakeUpdate(callback_query=history_query), ctx)
    )

    assert history_state == OrderStates.NONFOOD_CHOOSING_HISTORY
    assert _callback_data(history_message.edit_calls[-1]["reply_markup"]) == [
        "nfh:2026-04-21",
        "nfh:2026-04-19",
        "nfh:custom",
        "nfh:back",
    ]

    history_pick_message = _FakeMessage()
    history_pick_query = _FakeCallbackQuery("nfh:2026-04-19", history_pick_message)
    history_pick_state = asyncio.run(
        module.handle_nonfood_history_entry(
            _FakeUpdate(callback_query=history_pick_query),
            ctx,
        )
    )

    assert history_pick_state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"] == _order_map(HISTORY_ITEMS)

    custom_history_message = _FakeMessage()
    custom_history_query = _FakeCallbackQuery("nfh:custom", custom_history_message)
    custom_history_state = asyncio.run(
        module.handle_nonfood_history_entry(
            _FakeUpdate(callback_query=custom_history_query),
            ctx,
        )
    )

    assert custom_history_state == OrderStates.NONFOOD_ENTERING_HISTORY_DATE
    assert "DD/MM/YYYY" in custom_history_message.edit_calls[-1]["text"]

    invalid_date_message = _FakeMessage(text="not-a-date")
    invalid_date_state = asyncio.run(
        module.receive_nonfood_history_date(_FakeUpdate(message=invalid_date_message), ctx)
    )

    assert invalid_date_state == OrderStates.NONFOOD_ENTERING_HISTORY_DATE
    assert "Sai định dạng" in invalid_date_message.reply_calls[-1]["text"]

    valid_date_message = _FakeMessage(text="19/04/2026")
    valid_date_state = asyncio.run(
        module.receive_nonfood_history_date(_FakeUpdate(message=valid_date_message), ctx)
    )

    assert valid_date_state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"] == _order_map(HISTORY_ITEMS)

    history_back_message = _FakeMessage()
    history_back_state = asyncio.run(
        module.handle_nonfood_history_entry(
            _FakeUpdate(callback_query=_FakeCallbackQuery("nfh:back", history_back_message)),
            ctx,
        )
    )

    assert history_back_state == OrderStates.NONFOOD_ENTRY_POINT
    assert _callback_data(history_back_message.edit_calls[-1]["reply_markup"]) == [
        "nfe:recent",
        "nfe:tmpls",
        "nfe:hist",
        "nfe:new",
    ]


def test_nonfood_disabled_message():
    module = _import_nonfood_entry_module()

    ctx = _FakeContext(
        user_data={"order": {"F01": {"code": "F01"}}, "other_key": "keep-me"},
        bot_data={"nonfood_enabled": False},
    )
    message = _FakeMessage()

    state = asyncio.run(module.cmd_order_nonfood(_FakeUpdate(message=message), ctx))

    assert state is module.ConversationHandler.END
    assert message.reply_calls[-1]["text"].startswith("🙏 Đơn non-food đang tạm thời chưa sẵn sàng")
    assert ctx.user_data == {"order": {"F01": {"code": "F01"}}, "other_key": "keep-me"}


# ─── Non-food category browsing tests ────────────────────────────────────────


def _import_nonfood_category_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_category_module"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "handlers"
        / "conversation"
        / "nonfood_category.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


BOT_DATA_WITH_NONFOOD_CATALOG = {
    "nonfood_enabled": True,
    "nonfood_categories": {
        "Văn phòng": [
            {
                "code": "NF01",
                "name": "Giấy A4",
                "unit": "ram",
                "cat": "Văn phòng",
                "source": "CCDC",
            },
            {
                "code": "NF02",
                "name": "Bút bi",
                "unit": "cây",
                "cat": "Văn phòng",
                "source": "VTTH",
            },
        ],
        "Vệ sinh": [
            {
                "code": "NF03",
                "name": "Xà bông",
                "unit": "bịch",
                "cat": "Vệ sinh",
                "source": "CCDC",
            },
        ],
    },
    "nonfood_items": {
        "NF01": {
            "code": "NF01",
            "name": "Giấy A4",
            "unit": "ram",
            "cat": "Văn phòng",
            "source": "CCDC",
        },
        "NF02": {
            "code": "NF02",
            "name": "Bút bi",
            "unit": "cây",
            "cat": "Văn phòng",
            "source": "VTTH",
        },
        "NF03": {
            "code": "NF03",
            "name": "Xà bông",
            "unit": "bịch",
            "cat": "Vệ sinh",
            "source": "CCDC",
        },
    },
}


def test_category_browse_adds_item(monkeypatch):
    """Full browse: entry → pick cat → pick item → enter qty → item in nonfood_order."""
    module = _import_nonfood_category_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Step 1: Entry via nf:add_item → shows categories
    add_item_query = _FakeCallbackQuery("nf:add_item", _FakeMessage())
    state = asyncio.run(module.show_cats(_FakeUpdate(callback_query=add_item_query), ctx))
    assert state == OrderStates.NONFOOD_CHOOSING_CAT
    assert add_item_query.answer_calls == [{"text": None, "show_alert": False}]
    cat_markup = add_item_query.message.edit_calls[-1]["reply_markup"]
    assert _callback_data(cat_markup) == [
        "nfcat:Văn phòng",
        "nfcat:Vệ sinh",
        "nfcat:back",
    ]

    # Step 2: Pick category nfcat:Văn phòng → shows items with [CCDC]/[VTTH] badges
    cat_pick_query = _FakeCallbackQuery("nfcat:Văn phòng", _FakeMessage())
    state = asyncio.run(module.show_items(_FakeUpdate(callback_query=cat_pick_query), ctx))
    assert state == OrderStates.NONFOOD_CHOOSING_ITEM
    assert ctx.user_data["nf_current_cat"] == "Văn phòng"
    item_markup = cat_pick_query.message.edit_calls[-1]["reply_markup"]
    item_cbs = _callback_data(item_markup)
    assert "nfitem:NF01" in item_cbs
    assert "nfitem:NF02" in item_cbs
    # Verify source badges are rendered in button text
    item_texts = _button_texts(item_markup)
    assert any("[CCDC]" in t for t in item_texts)
    assert any("[VTTH]" in t for t in item_texts)

    # Step 3: Pick item nfitem:NF01 → prompts for qty
    item_pick_query = _FakeCallbackQuery("nfitem:NF01", _FakeMessage())
    state = asyncio.run(module.ask_qty(_FakeUpdate(callback_query=item_pick_query), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY
    assert ctx.user_data["nf_current_item"]["code"] == "NF01"
    qty_prompt_text = item_pick_query.message.reply_calls[-1]["text"]
    assert "Giấy A4" in qty_prompt_text
    assert "ram" in qty_prompt_text

    # Step 4: Enter valid qty → item added to nonfood_order with source
    qty_message = _FakeMessage(text="3")
    state = asyncio.run(module.receive_qty(_FakeUpdate(message=qty_message), ctx))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF01" in ctx.user_data["nonfood_order"]
    item_payload = ctx.user_data["nonfood_order"]["NF01"]
    assert item_payload["code"] == "NF01"
    assert item_payload["name"] == "Giấy A4"
    assert item_payload["qty"] == 3.0
    assert item_payload["unit"] == "ram"
    assert item_payload["source"] == "CCDC"

    # Step 5: Back from items → back to cats
    back_items_query = _FakeCallbackQuery("nfitem:back", _FakeMessage())
    state = asyncio.run(module.show_items(_FakeUpdate(callback_query=back_items_query), ctx))
    assert state == OrderStates.NONFOOD_CHOOSING_CAT

    # Step 6: Back from cats → returns NONFOOD_EDITING
    back_cats_query = _FakeCallbackQuery("nfcat:back", _FakeMessage())
    state = asyncio.run(module.show_items(_FakeUpdate(callback_query=back_cats_query), ctx))
    assert state == OrderStates.NONFOOD_EDITING

    # Step 7: qty=0 removes item from nonfood_order
    ctx.user_data["nonfood_order"] = {
        "NF01": {
            "code": "NF01",
            "name": "Giấy A4",
            "qty": 5,
            "unit": "ram",
            "source": "CCDC",
        }
    }
    ctx.user_data["nf_current_item"] = ctx.bot_data["nonfood_items"]["NF01"]
    qty_zero_message = _FakeMessage(text="0")
    state = asyncio.run(module.receive_qty(_FakeUpdate(message=qty_zero_message), ctx))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF01" not in ctx.user_data["nonfood_order"]


def test_category_invalid_quantity_reprompt(monkeypatch):
    """Non-numeric or negative quantity keeps user in NONFOOD_ENTERING_QTY state."""
    module = _import_nonfood_category_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},
            "nonfood_order_date": date(2026, 4, 21),
            "nf_current_item": {
                "code": "NF01",
                "name": "Giấy A4",
                "unit": "ram",
                "source": "CCDC",
            },
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Non-numeric input → reprompt
    bad_msg = _FakeMessage(text="abc")
    state = asyncio.run(module.receive_qty(_FakeUpdate(message=bad_msg), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY
    assert "Nhập số hợp lệ" in bad_msg.reply_calls[-1]["text"]

    # Negative number → reprompt
    neg_msg = _FakeMessage(text="-2")
    state = asyncio.run(module.receive_qty(_FakeUpdate(message=neg_msg), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY
    assert "Không thể âm" in neg_msg.reply_calls[-1]["text"]

    # Float-ish with comma separator also works (valid)
    ctx.user_data["nf_current_item"] = {
        "code": "NF02",
        "name": "Bút bi",
        "unit": "cây",
        "source": "VTTH",
    }
    float_msg = _FakeMessage(text="2,5")
    state = asyncio.run(module.receive_qty(_FakeUpdate(message=float_msg), ctx))
    assert state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"]["NF02"]["qty"] == 2.5
    assert ctx.user_data["nonfood_order"]["NF02"]["source"] == "VTTH"


# ─── Non-food exact code search tests ────────────────────────────────────────


def _import_nonfood_search_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_search_module"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "handlers"
        / "conversation"
        / "nonfood_search.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_code_search_success(monkeypatch):
    """Trigger nfsearch: → type code → matched item prompts qty → enter qty → item in nonfood_order."""
    module = _import_nonfood_search_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Step 1: Entry via nfsearch: → prompts for code
    search_query = _FakeCallbackQuery("nfsearch:", _FakeMessage())
    state = asyncio.run(module.start_search(_FakeUpdate(callback_query=search_query), ctx))
    assert state == OrderStates.NONFOOD_SEARCHING
    assert search_query.answer_calls == [{"text": None, "show_alert": False}]
    assert "Nhập mã sản phẩm" in search_query.message.reply_calls[-1]["text"]

    # Step 2: Type valid code → matched item prompts qty
    code_msg = _FakeMessage(text="NF01")
    state = asyncio.run(module.receive_search_code(_FakeUpdate(message=code_msg), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY
    assert ctx.user_data["nf_current_item"]["code"] == "NF01"
    assert ctx.user_data["nf_current_item"]["source"] == "CCDC"
    qty_prompt = code_msg.reply_calls[-1]["text"]
    assert "Giấy A4" in qty_prompt
    assert "ram" in qty_prompt

    # Step 3: Enter valid qty → item added to nonfood_order with source
    qty_msg = _FakeMessage(text="5")
    state = asyncio.run(module.receive_search_qty(_FakeUpdate(message=qty_msg), ctx))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF01" in ctx.user_data["nonfood_order"]
    item_payload = ctx.user_data["nonfood_order"]["NF01"]
    assert item_payload["code"] == "NF01"
    assert item_payload["name"] == "Giấy A4"
    assert item_payload["qty"] == 5.0
    assert item_payload["unit"] == "ram"
    assert item_payload["source"] == "CCDC"

    # Step 4: Search another code (NF02) → qty=0 removes item
    ctx.user_data["nonfood_order"] = {
        "NF01": {
            "code": "NF01",
            "name": "Giấy A4",
            "qty": 5,
            "unit": "ram",
            "source": "CCDC",
        }
    }
    ctx.user_data["nf_current_item"] = ctx.bot_data["nonfood_items"]["NF02"]
    qty_zero_msg = _FakeMessage(text="0")
    state = asyncio.run(module.receive_search_qty(_FakeUpdate(message=qty_zero_msg), ctx))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF02" not in ctx.user_data["nonfood_order"]


def test_exact_code_search_not_found(monkeypatch):
    """Unknown code → retry message, stays in NONFOOD_SEARCHING state."""
    module = _import_nonfood_search_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Step 1: Entry via nfsearch:
    search_query = _FakeCallbackQuery("nfsearch:", _FakeMessage())
    state = asyncio.run(module.start_search(_FakeUpdate(callback_query=search_query), ctx))
    assert state == OrderStates.NONFOOD_SEARCHING

    # Step 2: Type unknown code → retry, stays in search state
    bad_msg = _FakeMessage(text="BADCODE")
    state = asyncio.run(module.receive_search_code(_FakeUpdate(message=bad_msg), ctx))
    assert state == OrderStates.NONFOOD_SEARCHING
    assert "BADCODE" in bad_msg.reply_calls[-1]["text"]
    assert "Không tìm thấy" in bad_msg.reply_calls[-1]["text"]

    # Step 3: Invalid (non-numeric) qty after match → reprompt, stays in qty state
    # First enter a valid code to get to qty state
    good_code_msg = _FakeMessage(text="NF01")
    state = asyncio.run(module.receive_search_code(_FakeUpdate(message=good_code_msg), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY

    bad_qty_msg = _FakeMessage(text="abc")
    state = asyncio.run(module.receive_search_qty(_FakeUpdate(message=bad_qty_msg), ctx))
    assert state == OrderStates.NONFOOD_ENTERING_QTY
    assert "Nhập số hợp lệ" in bad_qty_msg.reply_calls[-1]["text"]

    # Step 4: "back" during code entry → returns to NONFOOD_EDITING
    back_msg = _FakeMessage(text="back")
    state = asyncio.run(module.receive_search_code(_FakeUpdate(message=back_msg), ctx))
    assert state is module.ConversationHandler.END


# ─── Non-food editing tests ────────────────────────────────────────────────────


def _import_nonfood_editing_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_editing_module"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "handlers"
        / "conversation"
        / "nonfood_editing.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_edit_and_remove_nonfood_item(monkeypatch):
    """Edit screen shows item → click edit → keypad → set qty → verify updated; remove → gone."""
    module = _import_nonfood_editing_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {
                    "code": "NF01",
                    "name": "Giấy A4",
                    "qty": 2,
                    "unit": "ram",
                    "source": "CCDC",
                }
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Step 1: Click edit on NF01 → shows keypad with current qty
    edit_query = _FakeCallbackQuery("nfei:edit:NF01", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_menu(
        _FakeUpdate(callback_query=edit_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING_ITEM
    assert ctx.user_data["nf_editing_code"] == "NF01"
    keypad_text = edit_query.message.edit_calls[-1]["text"]
    assert "Giấy A4" in keypad_text
    assert "2" in keypad_text  # current qty shown
    assert "[CCDC]" in keypad_text  # source shown

    # Step 2: Set preset qty (button "7") → qty updated, back to edit screen
    preset_query = _FakeCallbackQuery("nfeq:7", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_qty(
        _FakeUpdate(callback_query=preset_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"]["NF01"]["qty"] == 7.0

    # Step 3: Custom qty: click "Nhập số khác" → enters custom qty state
    custom_query = _FakeCallbackQuery("nfeq:custom", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_qty(
        _FakeUpdate(callback_query=custom_query), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_EDIT_QTY
    custom_text = custom_query.message.edit_calls[-1]["text"]
    assert "Giấy A4" in custom_text

    # Step 4: Enter valid custom qty → updated, returns to edit screen
    custom_msg = _FakeMessage(text="4")
    state = asyncio.run(module.receive_nonfood_edit_qty(
        _FakeUpdate(message=custom_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert ctx.user_data["nonfood_order"]["NF01"]["qty"] == 4.0

    # Step 5: Remove item → item gone, back to edit screen
    remove_query = _FakeCallbackQuery("nfeq:remove", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_qty(
        _FakeUpdate(callback_query=remove_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF01" not in ctx.user_data["nonfood_order"]

    # Step 6: Back from keypad → returns to edit screen
    back_query = _FakeCallbackQuery("nfeq:back", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_qty(
        _FakeUpdate(callback_query=back_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING

    # Step 7: qty=0 in custom input also removes item
    ctx.user_data["nonfood_order"] = {
        "NF01": {
            "code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC",
        }
    }
    ctx.user_data["nf_editing_code"] = "NF01"
    zero_msg = _FakeMessage(text="0")
    state = asyncio.run(module.receive_nonfood_edit_qty(
        _FakeUpdate(message=zero_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF01" not in ctx.user_data["nonfood_order"]


def test_nonfood_cannot_confirm_empty_order(monkeypatch):
    """Empty order + confirm → error message, stays in NONFOOD_EDITING."""
    module = _import_nonfood_editing_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},  # empty
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    # Empty order → confirm → error, stays in NONFOOD_EDITING
    confirm_query = _FakeCallbackQuery("nfe:confirm", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_menu(
        _FakeUpdate(callback_query=confirm_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert "Đơn trống" in confirm_query.message.reply_calls[-1]["text"]

    # Non-empty order → confirm → goes to NONFOOD_CONFIRM_ORDER
    ctx.user_data["nonfood_order"] = {
        "NF01": {
            "code": "NF01", "name": "Giấy A4", "qty": 1, "unit": "ram", "source": "CCDC",
        }
    }
    confirm_query2 = _FakeCallbackQuery("nfe:confirm", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_edit_menu(
        _FakeUpdate(callback_query=confirm_query2), ctx
    ))
    assert state == OrderStates.NONFOOD_CONFIRM_ORDER


# ─── Non-food template tests ──────────────────────────────────────────────────


def _import_nonfood_template_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_template_module"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "handlers"
        / "conversation"
        / "nonfood_template.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_save_new_nonfood_template(monkeypatch):
    """nfe:save → template menu → nftpl:new → enter name → saved, reply confirmed."""
    module = _import_nonfood_template_module()

    saved_templates = []

    def _mock_save(name, items):
        saved_templates.append({"name": name, "items": items})

    def _mock_list():
        return [{"_id": "tpl-vp", "name": "Văn phòng", "items": []}]

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3.0, "unit": "ram", "source": "CCDC"},
                "NF02": {"code": "NF02", "name": "Bút bi", "qty": 5.0, "unit": "cây", "source": "VTTH"},
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    monkeypatch.setattr(data, "list_nonfood_templates", _mock_list)
    monkeypatch.setattr(data, "save_nonfood_template", _mock_save)

    # Step 1: Click nfe:save → shows template menu
    save_query = _FakeCallbackQuery("nfe:save", _FakeMessage())
    state = asyncio.run(module.show_nonfood_template_menu(
        _FakeUpdate(callback_query=save_query), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME
    menu_text = save_query.message.reply_calls[-1]["text"]
    assert "Lưu mẫu" in menu_text

    # Step 2: Click nftpl:new → prompts for name
    new_query = _FakeCallbackQuery("nftpl:new", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_template(
        _FakeUpdate(callback_query=new_query), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME
    prompt_text = new_query.message.reply_calls[-1]["text"]
    assert "Nhập tên mẫu mới" in prompt_text

    # Step 3: Enter new name → saved, reply confirmed
    name_msg = _FakeMessage(text="Đơn thường")
    state = asyncio.run(module.receive_nonfood_template_name(
        _FakeUpdate(message=name_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert len(saved_templates) == 1
    assert saved_templates[0]["name"] == "Đơn thường"
    assert len(saved_templates[0]["items"]) == 2
    assert "Đã lưu mẫu" in name_msg.reply_calls[-1]["text"]


def test_overwrite_nonfood_template(monkeypatch):
    """Enter existing name → overwrite confirm → nftpl:overwrite → overwritten."""
    module = _import_nonfood_template_module()

    overwrite_calls = []

    def _mock_save(name, items):
        overwrite_calls.append({"name": name, "items": items})

    def _mock_list():
        return [{"_id": "tpl-vp", "name": "Văn phòng", "items": [{"code": "OLD", "name": "Old", "qty": 1, "unit": "cai"}]}]

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3.0, "unit": "ram", "source": "CCDC"},
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    monkeypatch.setattr(data, "list_nonfood_templates", _mock_list)
    monkeypatch.setattr(data, "save_nonfood_template", _mock_save)
    monkeypatch.setattr(data, "get_nonfood_template", lambda tid: [{"code": "OLD", "name": "Old", "qty": 1, "unit": "cai"}] if tid == "tpl-vp" else [])

    # Step 1: Enter existing template name → asks overwrite confirm
    name_msg = _FakeMessage(text="Văn phòng")
    state = asyncio.run(module.receive_nonfood_template_name(
        _FakeUpdate(message=name_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME
    confirm_text = name_msg.reply_calls[-1]["text"]
    assert "đã tồn tại" in confirm_text
    assert "Ghi đè" in confirm_text

    # Step 2: Click nftpl:overwrite:tpl-vp → overwritten
    overwrite_query = _FakeCallbackQuery("nftpl:overwrite:tpl-vp", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_template(
        _FakeUpdate(callback_query=overwrite_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert len(overwrite_calls) == 1
    assert overwrite_calls[0]["name"] == "tpl-vp"
    assert overwrite_calls[0]["items"][0]["code"] == "NF01"

    # Step 3: nftpl:back during name entry → back to editing
    ctx.user_data["nonfood_order"] = {
        "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 2, "unit": "ram", "source": "CCDC"},
    }
    back_query = _FakeCallbackQuery("nftpl:back", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_template(
        _FakeUpdate(callback_query=back_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING


def test_template_load_from_menu(monkeypatch):
    """nftpl:{id} → items loaded into nonfood_order → NONFOOD_EDITING."""
    module = _import_nonfood_template_module()

    def _mock_get(template_id):
        if template_id == "tpl-vp":
            return [
                {"code": "NF03", "name": "Xà bông", "qty": 4, "unit": "bịch", "source": "CCDC"},
                {"code": "NF01", "name": "Giấy A4", "qty": 1, "unit": "ram", "source": "CCDC"},
            ]
        return []

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    monkeypatch.setattr(data, "get_nonfood_template", _mock_get)

    # Step 1: Click nftpl:tpl-vp → items loaded, back to edit screen
    load_query = _FakeCallbackQuery("nftpl:tpl-vp", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_template(
        _FakeUpdate(callback_query=load_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
    assert "NF03" in ctx.user_data["nonfood_order"]
    assert ctx.user_data["nonfood_order"]["NF03"]["qty"] == 4
    assert ctx.user_data["nonfood_order"]["NF03"]["source"] == "CCDC"
    assert "NF01" in ctx.user_data["nonfood_order"]


# ─── Non-food confirm / date / cancel tests ────────────────────────────────────


def _import_nonfood_confirm_module():
    _install_telegram_stubs()
    module_name = "test_nonfood_confirm_module"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "handlers"
        / "conversation"
        / "nonfood_confirm.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_confirm_screen_shows_items_and_date(monkeypatch):
    """show_nonfood_confirm_screen renders items with source badges and current date."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"},
                "NF02": {"code": "NF02", "name": "Bút bi", "qty": 5, "unit": "cây", "source": "VTTH"},
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data={},
    )

    query = _FakeCallbackQuery("nfeq:confirm", _FakeMessage())
    state = asyncio.run(module.show_nonfood_confirm_screen(
        _FakeUpdate(callback_query=query), ctx
    ))
    assert state == OrderStates.NONFOOD_CONFIRM_ORDER
    edit_text = query.message.edit_calls[-1]["text"]
    assert "Giấy A4" in edit_text
    assert "3" in edit_text
    assert "CCDC" in edit_text
    assert "Bút bi" in edit_text
    assert "5" in edit_text
    assert "VTTH" in edit_text
    assert "21/04/2026" in edit_text


def test_confirm_cancel_resets_session(monkeypatch):
    """nfeq:cancel → session keys cleared, ConversationHandler.END returned."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"},
            },
            "nonfood_order_date": date(2026, 4, 21),
            "nf_current_cat": "Văn phòng",
        },
        bot_data={},
    )

    query = _FakeCallbackQuery("nfeq:cancel", _FakeMessage())
    state = asyncio.run(module.receive_nonfood_confirm(
        _FakeUpdate(callback_query=query), ctx
    ))
    assert state == module.ConversationHandler.END
    assert "nonfood_order" not in ctx.user_data
    assert "nonfood_order_date" not in ctx.user_data
    assert "nf_current_cat" not in ctx.user_data
    assert query.answer_calls == [{"text": None, "show_alert": False}]


def test_confirm_date_picks_quick_option(monkeypatch):
    """nfeq:date → date menu → pick tomorrow → confirm screen reflects new date."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"},
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data={},
    )

    # nfeq:date → shows date menu
    date_menu_query = _FakeCallbackQuery("nfeq:date", _FakeMessage())
    state = asyncio.run(module.receive_nonfood_confirm(
        _FakeUpdate(callback_query=date_menu_query), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_DATE
    date_menu_text = date_menu_query.message.edit_calls[-1]["text"]
    assert "Chọn ngày" in date_menu_text
    date_cbs = _callback_data(date_menu_query.message.edit_calls[-1]["reply_markup"])
    assert any("nfqdate:2026-04-22" in cb for cb in date_cbs)  # tomorrow

    # Pick tomorrow (2026-04-22)
    tomorrow_query = _FakeCallbackQuery("nfqdate:2026-04-22", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_date_choice(
        _FakeUpdate(callback_query=tomorrow_query), ctx
    ))
    assert state == OrderStates.NONFOOD_CONFIRM_ORDER
    assert ctx.user_data["nonfood_order_date"] == date(2026, 4, 22)
    confirm_text = tomorrow_query.message.edit_calls[-1]["text"]
    assert "22/04/2026" in confirm_text
    assert "ngày mai" in confirm_text


def test_confirm_date_custom_input(monkeypatch):
    """nfqdate:custom → enter DD/MM/YYYY → date updated on confirm screen."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {
                "NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"},
            },
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data={},
    )

    # nfqdate:custom → prompts for DD/MM/YYYY
    custom_query = _FakeCallbackQuery("nfqdate:custom", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_date_choice(
        _FakeUpdate(callback_query=custom_query), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_DATE
    custom_text = custom_query.message.edit_calls[-1]["text"]
    assert "DD/MM/YYYY" in custom_text

    # Enter valid custom date
    date_msg = _FakeMessage(text="30/05/2026")
    state = asyncio.run(module.receive_nonfood_date(
        _FakeUpdate(message=date_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_CONFIRM_ORDER
    assert ctx.user_data["nonfood_order_date"] == date(2026, 5, 30)


def test_confirm_date_invalid_input_reprompt(monkeypatch):
    """Bad format DD/MM/YYYY → reprompt, stays in NONFOOD_ENTERING_DATE."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {"NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"}},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data={},
    )

    bad_msg = _FakeMessage(text="not-a-date")
    state = asyncio.run(module.receive_nonfood_date(
        _FakeUpdate(message=bad_msg), ctx
    ))
    assert state == OrderStates.NONFOOD_ENTERING_DATE
    assert "Sai định dạng" in bad_msg.reply_calls[-1]["text"]


def test_confirm_date_back_returns_to_confirm(monkeypatch):
    """nfqdate:back from date menu → back to confirm screen."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {"NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"}},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data={},
    )

    back_query = _FakeCallbackQuery("nfqdate:back", _FakeMessage())
    state = asyncio.run(module.handle_nonfood_date_choice(
        _FakeUpdate(callback_query=back_query), ctx
    ))
    assert state == OrderStates.NONFOOD_CONFIRM_ORDER


def test_confirm_edit_returns_to_edit_screen(monkeypatch):
    """nfeq:edit → returns to NONFOOD_EDITING."""
    module = _import_nonfood_confirm_module()

    ctx = _FakeContext(
        user_data={
            "nonfood_order": {"NF01": {"code": "NF01", "name": "Giấy A4", "qty": 3, "unit": "ram", "source": "CCDC"}},
            "nonfood_order_date": date(2026, 4, 21),
        },
        bot_data=dict(BOT_DATA_WITH_NONFOOD_CATALOG),
    )

    edit_query = _FakeCallbackQuery("nfeq:edit", _FakeMessage())
    state = asyncio.run(module.receive_nonfood_confirm(
        _FakeUpdate(callback_query=edit_query), ctx
    ))
    assert state == OrderStates.NONFOOD_EDITING
