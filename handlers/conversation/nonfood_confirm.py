"""Non-food confirm screen, date selection, Excel export, and order save flow."""
from datetime import date, timedelta
from typing import Any, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler, filters, MessageHandler

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _date_label(d: date) -> str:
    delta = (d - date.today()).days
    suf = {-1: " (hôm qua)", 0: " (hôm nay)", 1: " (ngày mai)"}.get(delta, "")
    return f"{_fmt_date(d)}{suf}"


async def show_nonfood_confirm_screen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show non-food order confirmation screen with source badges."""
    from handlers.conversation.nonfood_entry import NONFOOD_SESSION_KEYS

    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    order_date = ctx.user_data.get("nonfood_order_date", date.today())

    lines = ["📋 *Xác nhận đơn non-food:*\n"]
    for item in nonfood_order.values():
        lines.append(
            f"  • {item['name']}: *{_fmt_qty(item['qty'])} {item['unit']}* [{item.get('source', '')}]"
        )
    lines.append(f"\n📅 *Ngày:* {_date_label(order_date)}\n_Tổng: {len(nonfood_order)} mặt hàng_")

    btns = [
        [InlineKeyboardButton("✅ Xác nhận đặt hàng", callback_data="nfeq:confirm")],
        [InlineKeyboardButton("📅 Chọn ngày giao hàng", callback_data="nfeq:date")],
        [InlineKeyboardButton("✏️ Sửa lại đơn", callback_data="nfeq:edit")],
        [InlineKeyboardButton("❌ Huỷ", callback_data="nfeq:cancel")],
    ]

    msg = getattr(update, "message", None) or update.callback_query.message
    try:
        await msg.edit_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
    except Exception:
        await msg.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
    return OrderStates.NONFOOD_CONFIRM_ORDER


async def receive_nonfood_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle nfeq:* callbacks in NONFOOD_CONFIRM_ORDER state."""
    from handlers.conversation.nonfood_entry import NONFOOD_SESSION_KEYS

    q = update.callback_query
    await q.answer()
    raw = q.data or ""

    if raw == "nfeq:edit":
        from handlers.conversation.nonfood_category import _show_nonfood_edit_screen
        return await _show_nonfood_edit_screen(update, ctx)

    if raw == "nfeq:date":
        return await show_nonfood_date_menu(update, ctx)

    if raw == "nfeq:cancel":
        for key in NONFOOD_SESSION_KEYS:
            ctx.user_data.pop(key, None)
        await q.message.reply_text("❌ Đã huỷ. Gõ /order_nonfood để bắt đầu lại.")
        return ConversationHandler.END

    if raw == "nfeq:confirm":
        return await _do_nonfood_export(update, ctx)

    return OrderStates.NONFOOD_CONFIRM_ORDER


async def show_nonfood_date_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show date selection quick options."""
    q = update.callback_query
    await q.answer()

    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    btns = [
        [InlineKeyboardButton(
            f"📅 {_fmt_date(today)} (hôm nay)",
            callback_data=f"nfqdate:{today.isoformat()}")],
        [InlineKeyboardButton(
            f"➡️ {_fmt_date(tomorrow)} (ngày mai)",
            callback_data=f"nfqdate:{tomorrow.isoformat()}")],
        [InlineKeyboardButton(
            f"➡️ {_fmt_date(day_after)}",
            callback_data=f"nfqdate:{day_after.isoformat()}")],
        [InlineKeyboardButton("📅 Nhập ngày khác (DD/MM/YYYY)", callback_data="nfqdate:custom")],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="nfqdate:back")],
    ]

    await q.message.edit_text(
        "📅 *Chọn ngày giao hàng:*",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_ENTERING_DATE


async def handle_nonfood_date_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle nfqdate:* callbacks in NONFOOD_ENTERING_DATE state."""
    q = update.callback_query
    await q.answer()
    raw = q.data or ""
    user_data = cast(dict[str, Any], ctx.user_data)

    if raw == "nfqdate:custom":
        await q.message.edit_text(
            "✏️ Nhập ngày *DD/MM/YYYY*\nVD: `25/12/2025`",
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_DATE

    if raw == "nfqdate:back":
        return await show_nonfood_confirm_screen(update, ctx)

    # Quick date pick
    date_iso = raw.replace("nfqdate:", "", 1)
    try:
        chosen = date.fromisoformat(date_iso)
    except ValueError:
        return OrderStates.NONFOOD_ENTERING_DATE

    user_data["nonfood_order_date"] = chosen
    return await show_nonfood_confirm_screen(update, ctx)


async def receive_nonfood_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom date input in NONFOOD_ENTERING_DATE state."""
    message = update.message
    assert message is not None
    user_data = cast(dict[str, Any], ctx.user_data)

    raw = message.text.strip()
    try:
        chosen = date(int(raw[6:10]), int(raw[3:5]), int(raw[0:2]))
    except Exception:
        await message.reply_text("⚠️ Sai định dạng. Nhập lại *DD/MM/YYYY*:", parse_mode="Markdown")
        return OrderStates.NONFOOD_ENTERING_DATE

    user_data["nonfood_order_date"] = chosen
    return await show_nonfood_confirm_screen(update, ctx)


async def _do_nonfood_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Build Excel, save to MongoDB, send document, reset session."""
    from handlers.conversation.nonfood_entry import NONFOOD_SESSION_KEYS
    import logging

    q = update.callback_query
    await q.answer("⏳ Đang tạo file...")

    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    order_date = ctx.user_data.get("nonfood_order_date", date.today())

    items_list = [
        {
            "code": code,
            "name": item["name"],
            "qty": item["qty"],
            "unit": item["unit"],
            "source": item.get("source", ""),
        }
        for code, item in nonfood_order.items()
    ]

    try:
        excel_svc = ctx.bot_data.get("nonfood_excel_service")
        if excel_svc is None:
            raise RuntimeError("nonfood_excel_service not available")

        buf = excel_svc.build_order_excel_nonfood(items_list, order_date)

        from data import save_nonfood_order
        save_nonfood_order(order_date, items_list)

        filename = f"DonDatHangNonfood_{order_date.strftime('%d%m%Y')}.xlsx"
        await q.message.reply_document(
            document=buf,
            filename=filename,
            caption=(
                f"✅ *File đặt hàng non-food ngày {_fmt_date(order_date)}*\n"
                f"📦 {len(items_list)} mặt hàng\n"
                "_Gửi cho nhà cung cấp!_"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.exception("Error building non-food order")
        await q.message.reply_text("❌ Lỗi tạo file. Thử lại.")
        return OrderStates.NONFOOD_CONFIRM_ORDER

    # Reset session
    for key in NONFOOD_SESSION_KEYS:
        ctx.user_data.pop(key, None)

    return ConversationHandler.END
