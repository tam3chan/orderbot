"""Non-food entry point handlers — dedicated /order_nonfood entry/history flow."""
from datetime import date
from typing import Any, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from states import OrderStates


Item = dict[str, Any]
OrderMap = dict[str, Item]


NONFOOD_SESSION_KEYS = (
    "nonfood_order",
    "nonfood_order_date",
    "nf_current_cat",
    "nf_current_item",
    "nf_editing_code",
    "nf_search_query",
)


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _reset_nonfood_session(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = cast(dict[str, Any], ctx.user_data)
    for key in NONFOOD_SESSION_KEYS:
        user_data.pop(key, None)


def _items_to_order_map(items: list[Item] | None) -> OrderMap:
    return {str(item["code"]): item for item in (items or [])}


async def cmd_order_nonfood(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> Any:
    """Handle /order_nonfood command — show non-food entry menu."""
    message = update.message
    assert message is not None

    if not ctx.bot_data.get("nonfood_enabled"):
        _ = await message.reply_text(
            "🙏 Đơn non-food đang tạm thời chưa sẵn sàng. Vui lòng thử lại sau nhé."
        )
        return ConversationHandler.END

    _reset_nonfood_session(ctx)
    user_data = cast(dict[str, Any], ctx.user_data)
    user_data["nonfood_order"] = {}
    user_data["nonfood_order_date"] = date.today()

    _ = await message.reply_text(
        "🧾 *Bắt đầu đơn non-food từ đâu?*",
        reply_markup=_build_entry_markup(),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_ENTRY_POINT


def _build_entry_markup() -> InlineKeyboardMarkup:
    from data import get_nonfood_order, get_recent_nonfood_dates, list_nonfood_templates

    recent_dates = get_recent_nonfood_dates(1)
    templates = list_nonfood_templates()
    buttons: list[list[InlineKeyboardButton]] = []

    if recent_dates:
        recent_date = date.fromisoformat(recent_dates[0])
        count = len(get_nonfood_order(recent_date) or [])
        buttons.append([
            InlineKeyboardButton(
                f"🔄 Đơn non-food gần nhất ({_fmt_date(recent_date)} — {count} món)",
                callback_data="nfe:recent",
            )
        ])

    if len(templates) == 1:
        buttons.append([
            InlineKeyboardButton(
                f"📋 Từ mẫu non-food: {templates[0]['name']}",
                callback_data=f"nfe:tpl:{templates[0]['_id']}",
            )
        ])
    elif len(templates) > 1:
        buttons.append([
            InlineKeyboardButton("📋 Từ mẫu non-food đã lưu", callback_data="nfe:tmpls")
        ])

    buttons.append([
        InlineKeyboardButton("📅 Từ đơn non-food ngày khác", callback_data="nfe:hist")
    ])
    buttons.append([
        InlineKeyboardButton("✏️ Tạo đơn non-food mới", callback_data="nfe:new")
    ])

    return InlineKeyboardMarkup(buttons)


async def handle_nonfood_entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> Any:
    """Handle nfe:* callbacks in NONFOOD_ENTRY_POINT state."""
    from data import (
        get_nonfood_order,
        get_nonfood_template,
        get_recent_nonfood_dates,
    )
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen, show_cats

    query = update.callback_query
    assert query is not None
    _ = await query.answer()
    value = query.data or ""
    user_data = cast(dict[str, Any], ctx.user_data)

    if value == "nfe:new":
        user_data["nonfood_order"] = {}
        return await show_cats(update, ctx)

    if value == "nfe:recent":
        recent_dates = get_recent_nonfood_dates(1)
        if recent_dates:
            items = get_nonfood_order(date.fromisoformat(recent_dates[0]))
            user_data["nonfood_order"] = _items_to_order_map(items)
        return await _show_nonfood_edit_screen(update, ctx)

    if value == "nfe:hist":
        _ = await _show_history_menu(update)
        return OrderStates.NONFOOD_CHOOSING_HISTORY

    if value == "nfe:tmpls":
        _ = await _show_templates_menu(update)
        return OrderStates.NONFOOD_ENTRY_POINT

    if value.startswith("nfe:tpl:"):
        template_name = value.replace("nfe:tpl:", "", 1)
        items = get_nonfood_template(template_name)
        user_data["nonfood_order"] = _items_to_order_map(items)
        return await _show_nonfood_edit_screen(update, ctx)

    if value == "nfe:back_main":
        await _show_entry_point_menu(update)
        return OrderStates.NONFOOD_ENTRY_POINT

    return OrderStates.NONFOOD_ENTRY_POINT


async def _show_entry_point_menu(update: Update) -> None:
    query = update.callback_query
    assert query is not None
    message = cast(Any, query.message)
    _ = await message.edit_text(
        "🧾 *Bắt đầu đơn non-food từ đâu?*",
        reply_markup=_build_entry_markup(),
        parse_mode="Markdown",
    )


async def _show_templates_menu(update: Update) -> Any:
    from data import list_nonfood_templates

    templates = list_nonfood_templates()
    buttons = [
        [InlineKeyboardButton(f"📋 {template['name']}", callback_data=f"nfe:tpl:{template['_id']}")]
        for template in templates
    ]
    buttons.append([InlineKeyboardButton("↩️ Quay lại", callback_data="nfe:back_main")])

    query = update.callback_query
    assert query is not None
    message = cast(Any, query.message)

    _ = await message.edit_text(
        "📋 *Chọn mẫu non-food:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_ENTRY_POINT


async def _show_history_menu(update: Update) -> Any:
    from data import get_nonfood_order, get_recent_nonfood_dates

    recent_dates = get_recent_nonfood_dates(7)
    buttons: list[list[InlineKeyboardButton]] = []
    for iso_date in recent_dates:
        history_date = date.fromisoformat(iso_date)
        count = len(get_nonfood_order(history_date) or [])
        buttons.append([
            InlineKeyboardButton(
                f"📅 {_fmt_date(history_date)} — {count} món",
                callback_data=f"nfh:{iso_date}",
            )
        ])

    buttons.append([InlineKeyboardButton("🔍 Nhập ngày cụ thể", callback_data="nfh:custom")])
    buttons.append([InlineKeyboardButton("↩️ Quay lại", callback_data="nfh:back")])

    query = update.callback_query
    assert query is not None
    message = cast(Any, query.message)

    _ = await message.edit_text(
        "📅 *Chọn đơn non-food từ lịch sử:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_CHOOSING_HISTORY


async def handle_nonfood_history_entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> Any:
    """Handle nfh:* callbacks in NONFOOD_CHOOSING_HISTORY state."""
    from data import get_nonfood_order_by_iso
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen

    query = update.callback_query
    assert query is not None
    user_data = cast(dict[str, Any], ctx.user_data)

    _ = await query.answer()
    value = query.data or ""

    if value == "nfh:back":
        await _show_entry_point_menu(update)
        return OrderStates.NONFOOD_ENTRY_POINT

    if value == "nfh:custom":
        message = cast(Any, query.message)
        _ = await message.edit_text(
            "🔍 Nhập ngày non-food *DD/MM/YYYY*\nVD: `25/03/2026`",
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_HISTORY_DATE

    history_date = value.replace("nfh:", "", 1)
    items = get_nonfood_order_by_iso(history_date)
    if not items:
        _ = await query.answer("❌ Không tìm thấy đơn non-food ngày này", show_alert=True)
        return OrderStates.NONFOOD_ENTRY_POINT

    user_data["nonfood_order"] = _items_to_order_map(items)
    return await _show_nonfood_edit_screen(update, ctx)


async def receive_nonfood_history_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> Any:
    """Handle custom non-food history date input."""
    from data import get_nonfood_order
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen

    message = update.message
    assert message is not None
    user_data = cast(dict[str, Any], ctx.user_data)

    raw = cast(str, message.text).strip()
    try:
        history_date = date(int(raw[6:10]), int(raw[3:5]), int(raw[0:2]))
    except Exception:
        _ = await message.reply_text(
            "⚠️ Sai định dạng. Nhập lại *DD/MM/YYYY*: ",
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_HISTORY_DATE

    items = get_nonfood_order(history_date)
    if not items:
        _ = await message.reply_text(
            f"❌ Không có đơn non-food ngày {_fmt_date(history_date)}. Nhập ngày khác:"
        )
        return OrderStates.NONFOOD_ENTERING_HISTORY_DATE

    user_data["nonfood_order"] = _items_to_order_map(items)
    return await _show_nonfood_edit_screen(update, ctx)
