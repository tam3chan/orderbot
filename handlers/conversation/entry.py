"""Entry point handlers — ENTRY_POINT state + entry point conversation wiring."""
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from states import OrderStates


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


async def cmd_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /order command — show entry point menu."""
    ctx.user_data.clear()
    ctx.user_data["order"] = {}
    ctx.user_data["order_date"] = date.today()

    from data import get_recent_dates, list_templates, get_order

    recent = get_recent_dates(1)
    tmpls = list_templates()
    btns = []

    if recent:
        d = date.fromisoformat(recent[0])
        n = len(get_order(d) or [])
        btns.append([InlineKeyboardButton(
            f"🔄 Đơn gần nhất ({_fmt_date(d)} — {n} món)",
            callback_data="en:recent")])

    if len(tmpls) == 1:
        btns.append([InlineKeyboardButton(
            f"📋 Từ mẫu: {tmpls[0]['name']}",
            callback_data=f"en:tpl:{tmpls[0]['_id']}")])
    elif len(tmpls) > 1:
        btns.append([InlineKeyboardButton("📋 Từ mẫu đã lưu", callback_data="en:tmpls")])

    btns.append([InlineKeyboardButton("📅 Từ đơn ngày khác", callback_data="en:hist")])
    btns.append([InlineKeyboardButton("✏️ Tạo mới hoàn toàn", callback_data="en:new")])

    await update.message.reply_text(
        "🚀 *Bắt đầu đơn hàng từ đâu?*",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")
    return OrderStates.ENTRY_POINT


async def handle_entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle en:* callbacks in ENTRY_POINT state."""
    from handlers.conversation.editing import show_edit_screen

    q = update.callback_query
    await q.answer()
    v = q.data

    from data import get_recent_dates, get_order, get_template, list_templates

    if v == "en:new":
        ctx.user_data["order"] = {}
        return await show_edit_screen(update, ctx)

    elif v == "en:recent":
        dates = get_recent_dates(1)
        if dates:
            items = get_order(date.fromisoformat(dates[0]))
            ctx.user_data["order"] = {str(it["code"]): it for it in (items or [])}
        return await show_edit_screen(update, ctx)

    elif v == "en:hist":
        await _show_history_menu(update, ctx)
        return OrderStates.CHOOSING_HISTORY

    elif v == "en:tmpls":
        await _show_templates_menu(update, ctx)
        return OrderStates.ENTRY_POINT

    elif v.startswith("en:tpl:"):
        items = get_template(v.replace("en:tpl:", ""))
        ctx.user_data["order"] = {str(it["code"]): it for it in (items or [])}
        return await show_edit_screen(update, ctx)

    elif v == "en:back_main":
        await _show_entry_point_menu(update, ctx)
        return OrderStates.ENTRY_POINT

    return OrderStates.EDITING


async def _show_entry_point_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Rebuild and edit the entry point menu message (used for back navigation)."""
    from data import get_recent_dates, list_templates, get_order

    recent = get_recent_dates(1)
    tmpls = list_templates()
    btns = []

    if recent:
        d = date.fromisoformat(recent[0])
        n = len(get_order(d) or [])
        btns.append([InlineKeyboardButton(
            f"🔄 Đơn gần nhất ({_fmt_date(d)} — {n} món)",
            callback_data="en:recent")])

    if len(tmpls) == 1:
        btns.append([InlineKeyboardButton(
            f"📋 Từ mẫu: {tmpls[0]['name']}",
            callback_data=f"en:tpl:{tmpls[0]['_id']}")])
    elif len(tmpls) > 1:
        btns.append([InlineKeyboardButton("📋 Từ mẫu đã lưu", callback_data="en:tmpls")])

    btns.append([InlineKeyboardButton("📅 Từ đơn ngày khác", callback_data="en:hist")])
    btns.append([InlineKeyboardButton("✏️ Tạo mới hoàn toàn", callback_data="en:new")])

    await update.callback_query.message.edit_text(
        "🚀 *Bắt đầu đơn hàng từ đâu?*",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")


async def _show_templates_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show template selection menu."""
    from data import list_templates

    tmpls = list_templates()
    btns = [[InlineKeyboardButton(f"📋 {t['name']}", callback_data=f"en:tpl:{t['_id']}")]
            for t in tmpls]
    btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="en:back_main")])

    await update.callback_query.message.edit_text(
        "📋 *Chọn mẫu:*",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")
    return OrderStates.ENTRY_POINT


async def _show_history_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show history date selection menu."""
    from data import get_recent_dates, get_order

    dates = get_recent_dates(7)
    btns = []
    for ds in dates:
        d = date.fromisoformat(ds)
        n = len(get_order(d) or [])
        btns.append([InlineKeyboardButton(
            f"📅 {_fmt_date(d)} — {n} món",
            callback_data=f"hi:{ds}")])

    btns.append([InlineKeyboardButton("🔍 Nhập ngày cụ thể", callback_data="hi:custom")])
    btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="hi:back")])

    msg = update.callback_query.message if update.callback_query else update.message
    try:
        await msg.edit_text("📅 *Chọn đơn từ lịch sử:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown")
    except Exception:
        await msg.reply_text("📅 *Chọn đơn từ lịch sử:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown")
    return OrderStates.CHOOSING_HISTORY


async def handle_history_entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hi:* callbacks in CHOOSING_HISTORY state (entry point sub-flow)."""
    from handlers.conversation.editing import show_edit_screen
    from data import get_order_by_iso

    q = update.callback_query
    await q.answer()
    v = q.data

    if v == "hi:back":
        await _show_entry_point_menu(update, ctx)
        return OrderStates.ENTRY_POINT

    if v == "hi:custom":
        await q.message.edit_text(
            "🔍 Nhập ngày *DD/MM/YYYY*\nVD: `25/03/2026`",
            parse_mode="Markdown")
        return OrderStates.ENTERING_HISTORY_DATE

    ds = v.replace("hi:", "")
    items = get_order_by_iso(ds)
    if not items:
        await q.answer("❌ Không tìm thấy đơn ngày này", show_alert=True)
        return OrderStates.ENTRY_POINT

    ctx.user_data["order"] = {str(it["code"]): it for it in items}
    return await show_edit_screen(update, ctx)


async def receive_history_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom date input in ENTERING_HISTORY_DATE state."""
    from handlers.conversation.editing import show_edit_screen
    from data import get_order

    raw = update.message.text.strip()
    try:
        d = date(int(raw[6:10]), int(raw[3:5]), int(raw[0:2]))
    except Exception:
        await update.message.reply_text("⚠️ Sai định dạng. Nhập lại *DD/MM/YYYY*:",
            parse_mode="Markdown")
        return OrderStates.ENTERING_HISTORY_DATE

    items = get_order(d)
    if not items:
        await update.message.reply_text(
            f"❌ Không có đơn ngày {_fmt_date(d)}. Nhập ngày khác:")
        return OrderStates.ENTERING_HISTORY_DATE

    ctx.user_data["order"] = {str(it["code"]): it for it in items}
    return await show_edit_screen(update, ctx)
