"""History handlers — CHOOSING_HISTORY, ENTERING_HISTORY_DATE states."""
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from states import OrderStates


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


async def show_history_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
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


async def handle_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hi:* callbacks in CHOOSING_HISTORY state."""
    from data import get_order_by_iso, get_order

    q = update.callback_query
    await q.answer()
    v = q.data

    if v == "hi:back":
        from handlers.conversation.entry import _show_entry_point_menu
        await _show_entry_point_menu(update, ctx)
        return ConversationHandler.END

    if v == "hi:custom":
        await q.message.edit_text(
            "🔍 Nhập ngày *DD/MM/YYYY*\nVD: `25/03/2026`",
            parse_mode="Markdown")
        return OrderStates.ENTERING_HISTORY_DATE

    ds = v.replace("hi:", "")
    items = get_order_by_iso(ds)
    if not items:
        await q.answer("❌ Không tìm thấy đơn ngày này", show_alert=True)
        return OrderStates.CHOOSING_HISTORY

    ctx.user_data["order"] = {str(it["code"]): it for it in items}
    from handlers.conversation.editing import show_edit_screen
    return await show_edit_screen(update, ctx)


async def receive_history_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom date input in ENTERING_HISTORY_DATE state."""
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
    from handlers.conversation.editing import show_edit_screen
    return await show_edit_screen(update, ctx)


# Nested ConversationHandler for history sub-flow
history_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_history_menu, pattern=r"^en:hist$")],
    states={
        OrderStates.CHOOSING_HISTORY: [
            CallbackQueryHandler(handle_history, pattern=r"^hi:"),
        ],
        OrderStates.ENTERING_HISTORY_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_history_date),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.ENTRY_POINT,
    },
    fallbacks=[],
)
