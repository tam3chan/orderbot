"""Category browsing handlers — CHOOSING_CAT, CHOOSING_ITEM, ENTERING_QTY states."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


async def show_cats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show category selection keyboard."""
    cats = ctx.bot_data.get("categories", {})
    btns = [[InlineKeyboardButton(f"📁 {cat} ({len(items)})", callback_data=f"cat:{cat}")]
            for cat, items in cats.items()]
    btns.append([InlineKeyboardButton("↩️ Quay lại đơn", callback_data="cat:back")])

    msg = getattr(update, "message", None) or update.callback_query.message
    try:
        await msg.edit_text("📋 Chọn nhóm hàng:",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown")
    except Exception:
        await msg.reply_text("📋 Chọn nhóm hàng:",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown")
    return OrderStates.CHOOSING_CAT


async def show_items(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show items in selected category."""
    q = update.callback_query
    await q.answer()
    cat = q.data.replace("cat:", "")

    if cat == "back":
        return OrderStates.EDITING

    ctx.user_data["current_cat"] = cat
    cats = ctx.bot_data.get("categories", {})
    items = cats.get(cat, [])

    btns = []
    for it in items:
        lbl = f"{it['name']} ({it['unit']})"
        if len(lbl) > 40:
            lbl = lbl[:37] + "..."
        btns.append([InlineKeyboardButton(lbl, callback_data=f"item:{it['code']}")])

    btns.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="cat:back")])

    await q.message.edit_text(f"📁 *{cat}*\nChọn mặt hàng:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")
    return OrderStates.CHOOSING_ITEM


async def ask_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask user to enter quantity for selected item."""
    q = update.callback_query
    await q.answer()

    code = q.data.replace("item:", "")
    items = ctx.bot_data.get("items", {})
    item = items.get(code)

    if not item:
        await q.answer("Không tìm thấy mặt hàng!", show_alert=True)
        return OrderStates.CHOOSING_ITEM

    ctx.user_data["current_item"] = item
    existing = ctx.user_data["order"].get(code, {}).get("qty")
    hint = f" (hiện: {_fmt_qty(existing)})" if existing is not None else ""

    await q.message.reply_text(
        f"✏️ *{item['name']}* ({item['unit']}){hint}\n"
        "Nhập số lượng (0 = bỏ):",
        parse_mode="Markdown")
    return OrderStates.ENTERING_QTY


async def receive_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input and add item to order."""
    raw = update.message.text.strip().replace(",", ".")
    try:
        qty = float(raw)
    except ValueError:
        await update.message.reply_text("⚠️ Nhập số hợp lệ:")
        return OrderStates.ENTERING_QTY

    if qty < 0:
        await update.message.reply_text("⚠️ Không thể âm:")
        return OrderStates.ENTERING_QTY

    item = ctx.user_data.get("current_item")
    if not item:
        await update.message.reply_text("❌ Lỗi phiên. Gõ /order lại.")
        return ConversationHandler.END

    code = str(item["code"])
    if qty == 0:
        ctx.user_data["order"].pop(code, None)
    else:
        ctx.user_data["order"][code] = {
            "code": item["code"],
            "name": item["name"],
            "qty": qty,
            "unit": item["unit"],
            "ncc": item["ncc"],
        }

    from handlers.conversation.editing import show_edit_screen
    await show_edit_screen(update, ctx)
    return ConversationHandler.END


# Nested ConversationHandler for category browsing sub-flow
category_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_cats, pattern=r"^add_item$")],
    states={
        OrderStates.CHOOSING_CAT: [
            CallbackQueryHandler(show_items, pattern=r"^cat:"),
        ],
        OrderStates.CHOOSING_ITEM: [
            CallbackQueryHandler(ask_qty, pattern=r"^item:"),
            CallbackQueryHandler(show_cats, pattern=r"^cat:back$"),
        ],
        OrderStates.ENTERING_QTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.EDITING,
    },
    fallbacks=[],
)
