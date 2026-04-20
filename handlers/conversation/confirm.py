"""Confirmation handlers — CONFIRM_ORDER, ENTERING_DATE states."""
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _date_label(d: date) -> str:
    delta = (d - date.today()).days
    suf = {-1: " (hôm qua)", 0: " (hôm nay)", 1: " (ngày mai)"}.get(delta, "")
    return f"{_fmt_date(d)}{suf}"


def _confirm_markup(order: dict, order_date: date) -> tuple[str, InlineKeyboardMarkup]:
    """Build confirmation message and keyboard."""
    lines = ["📋 *Xác nhận đơn đặt hàng:*\n"]
    for v in order.values():
        lines.append(f"  • {v['name']}: *{_fmt_qty(v['qty'])} {v['unit']}*")
    lines.append(f"\n📅 *Ngày:* {_date_label(order_date)}\n_Tổng: {len(order)} mặt hàng_")

    btns = [
        [
            InlineKeyboardButton("✅ Tạo file Excel", callback_data="confirm_yes"),
            InlineKeyboardButton("📅 Đổi ngày", callback_data="change_date"),
        ],
        [
            InlineKeyboardButton("✏️ Sửa tiếp", callback_data="back_to_edit"),
            InlineKeyboardButton("❌ Huỷ", callback_data="confirm_no"),
        ],
    ]
    return "\n".join(lines), InlineKeyboardMarkup(btns)


async def show_confirm_screen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show order confirmation screen."""
    order = ctx.user_data.get("order", {})
    order_date = ctx.user_data.get("order_date", date.today())
    text, markup = _confirm_markup(order, order_date)

    msg = getattr(update, "message", None) or update.callback_query.message
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        await msg.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return OrderStates.CONFIRM_ORDER


async def confirm_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate Excel file and save order."""
    import logging
    from data import save_order
    from services.excel_service import ExcelService

    q = update.callback_query
    await q.answer("⏳ Đang tạo file...")

    order = ctx.user_data.get("order", {})
    order_date = ctx.user_data.get("order_date", date.today())
    items_list = list(order.values())

    try:
        excel_svc: ExcelService = ctx.bot_data["excel_service"]
        buf = excel_svc.build_order_excel(items_list, order_date)
        save_order(order_date, items_list)

        filename = f"DonDatHang_{order_date.strftime('%d%m%Y')}.xlsx"
        await q.message.reply_document(
            document=buf,
            filename=filename,
            caption=(
                f"✅ *File đặt hàng ngày {_fmt_date(order_date)}*\n"
                f"📦 {len(items_list)} mặt hàng\n"
                "_Gửi cho nhà cung cấp!_"
            ),
            parse_mode="Markdown")
    except Exception as e:
        logging.exception("Error building order")
        await q.message.reply_text("❌ Lỗi tạo file. Thử lại.")

    ctx.user_data.clear()
    return ConversationHandler.END


async def confirm_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel order."""
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("❌ Đã huỷ. Gõ /order để bắt đầu lại.")
    ctx.user_data.clear()
    return ConversationHandler.END


async def back_to_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to edit screen."""
    q = update.callback_query
    await q.answer()

    # Import here to avoid circular reference
    from handlers.conversation.editing import show_edit_screen
    return await show_edit_screen(update, ctx)


async def change_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show date selection keyboard."""
    q = update.callback_query
    await q.answer()

    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    btns = [
        [InlineKeyboardButton(
            f"⬅️ {_fmt_date(yesterday)} (hôm qua)",
            callback_data=f"qdate:{yesterday.isoformat()}")],
        [InlineKeyboardButton(
            f"📅 {_fmt_date(today)} (hôm nay)",
            callback_data=f"qdate:{today.isoformat()}")],
        [InlineKeyboardButton(
            f"➡️ {_fmt_date(tomorrow)} (ngày mai)",
            callback_data=f"qdate:{tomorrow.isoformat()}")],
        [InlineKeyboardButton(
            "✏️ Nhập ngày khác (DD/MM/YYYY)",
            callback_data="qdate:custom")],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="qdate:back")],
    ]

    await q.message.edit_text("📅 *Chọn ngày đặt hàng:*",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")
    return OrderStates.CONFIRM_ORDER


async def quick_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle qdate:* callbacks."""
    q = update.callback_query
    await q.answer()
    v = q.data.replace("qdate:", "")

    if v == "custom":
        await q.message.edit_text(
            "✏️ Nhập ngày *DD/MM/YYYY*\nVD: `25/12/2025`",
            parse_mode="Markdown")
        return OrderStates.ENTERING_DATE

    if v == "back":
        return await show_confirm_screen(update, ctx)

    order = ctx.user_data.get("order", {})
    chosen = date.fromisoformat(v)
    ctx.user_data["order_date"] = chosen

    text, markup = _confirm_markup(order, chosen)
    await q.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    return OrderStates.CONFIRM_ORDER


async def enter_custom_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom date input."""
    raw = update.message.text.strip()
    try:
        chosen = date(int(raw[6:10]), int(raw[3:5]), int(raw[0:2]))
    except Exception:
        await update.message.reply_text("⚠️ Sai định dạng. Nhập lại *DD/MM/YYYY*:",
            parse_mode="Markdown")
        return OrderStates.ENTERING_DATE

    ctx.user_data["order_date"] = chosen
    return await show_confirm_screen(update, ctx)


# Nested ConversationHandler for date selection sub-flow
date_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(change_date, pattern=r"^change_date$")],
    states={
        OrderStates.CONFIRM_ORDER: [
            CallbackQueryHandler(quick_date, pattern=r"^qdate:"),
        ],
        OrderStates.ENTERING_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_date),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.CONFIRM_ORDER,
    },
    fallbacks=[],
)
