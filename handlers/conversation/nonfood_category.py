"""Non-food category browsing handlers — NONFOOD_CHOOSING_CAT, NONFOOD_CHOOSING_ITEM, NONFOOD_ENTERING_QTY states."""
from typing import Any, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, filters, MessageHandler

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


async def show_cats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show non-food category selection keyboard."""
    q = update.callback_query
    await q.answer()
    cats = cast(dict, ctx.bot_data.get("nonfood_categories", {}))
    btns = [
        [InlineKeyboardButton(f"📁 {cat} ({len(items)})", callback_data=f"nfcat:{cat}")]
        for cat, items in cats.items()
    ]
    btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="nfcat:back")])

    msg = getattr(update, "message", None) or update.callback_query.message
    try:
        await msg.edit_text(
            "📋 *Chọn nhóm hàng non-food:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
    except Exception:
        await msg.reply_text(
            "📋 *Chọn nhóm hàng non-food:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
    return OrderStates.NONFOOD_CHOOSING_CAT


async def show_items(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show items in selected non-food category with source badges."""
    q = update.callback_query
    await q.answer()
    raw = q.data or ""

    # Back from items → return to cats
    if raw == "nfitem:back":
        return OrderStates.NONFOOD_CHOOSING_CAT

    # Back from cats → return to editing (via map_to_parent END → NONFOOD_EDITING)
    if raw == "nfcat:back":
        return OrderStates.NONFOOD_EDITING

    cat = raw.replace("nfcat:", "", 1)

    user_data = cast(dict[str, Any], ctx.user_data)
    user_data["nf_current_cat"] = cat

    cats = cast(dict, ctx.bot_data.get("nonfood_categories", {}))
    items = cats.get(cat, [])

    btns = []
    for it in items:
        lbl = f"{it['name']} ({it['unit']}) [{it['source']}]"
        if len(lbl) > 40:
            lbl = lbl[:37] + "..."
        btns.append([InlineKeyboardButton(lbl, callback_data=f"nfitem:{it['code']}")])

    btns.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="nfitem:back")])

    await q.message.edit_text(
        f"📁 *{cat}*\nChọn mặt hàng:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_CHOOSING_ITEM


async def ask_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask user to enter quantity for selected non-food item."""
    q = update.callback_query
    await q.answer()

    code = q.data.replace("nfitem:", "", 1)
    items = cast(dict, ctx.bot_data.get("nonfood_items", {}))
    item = items.get(code)

    if not item:
        await q.answer("Không tìm thấy mặt hàng!", show_alert=True)
        return OrderStates.NONFOOD_CHOOSING_ITEM

    user_data = cast(dict[str, Any], ctx.user_data)
    user_data["nf_current_item"] = item

    nonfood_order = cast(dict, user_data.get("nonfood_order", {}))
    existing = nonfood_order.get(code, {}).get("qty")
    hint = f" (hiện: {_fmt_qty(existing)})" if existing is not None else ""

    await q.message.reply_text(
        f"✏️ *{item['name']}* ({item['unit']}){hint}\n"
        "Nhập số lượng (0 = bỏ):",
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_ENTERING_QTY


async def receive_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input and add/remove item in nonfood_order."""
    message = update.message
    assert message is not None

    raw = message.text.strip().replace(",", ".")
    try:
        qty = float(raw)
    except ValueError:
        await message.reply_text("⚠️ Nhập số hợp lệ:")
        return OrderStates.NONFOOD_ENTERING_QTY

    if qty < 0:
        await message.reply_text("⚠️ Không thể âm:")
        return OrderStates.NONFOOD_ENTERING_QTY

    user_data = cast(dict[str, Any], ctx.user_data)
    item = user_data.get("nf_current_item")
    if not item:
        await message.reply_text("❌ Lỗi phiên. Gõ /order_nonfood lại.")
        return ConversationHandler.END

    code = str(item["code"])
    nonfood_order = cast(dict, user_data.get("nonfood_order", {}))
    user_data["nonfood_order"] = nonfood_order

    if qty == 0:
        nonfood_order.pop(code, None)
    else:
        nonfood_order[code] = {
            "code": item["code"],
            "name": item["name"],
            "qty": qty,
            "unit": item["unit"],
            "source": item["source"],
        }

    return await _show_nonfood_edit_screen(update, ctx)


async def _show_nonfood_edit_screen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the non-food order edit screen."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    btns: list[list[InlineKeyboardButton]] = []

    for code, item in nonfood_order.items():
        lbl = f"{item['name']}: {_fmt_qty(item['qty'])} {item['unit']}"
        if len(lbl) > 38:
            lbl = lbl[:35] + "..."
        btns.append([InlineKeyboardButton(f"✏️ {lbl}", callback_data=f"nfei:edit:{code}")])

    btns.append([InlineKeyboardButton("🔍 Tìm mã", callback_data="nfsearch:")])
    btns.append([InlineKeyboardButton("➕ Thêm mặt hàng", callback_data="nf:add_item")])
    btns.append([
        InlineKeyboardButton("✅ Xong – Xác nhận", callback_data="nfe:confirm"),
        InlineKeyboardButton("💾 Lưu mẫu", callback_data="nfe:save"),
    ])

    msg = getattr(update, "message", None) or update.callback_query.message
    text = f"✏️ *Đơn non-food ({len(nonfood_order)} món)* — Chạm để sửa:"
    try:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")
    except Exception:
        await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

    return OrderStates.NONFOOD_EDITING


# Nested ConversationHandler for non-food category browsing sub-flow
nonfood_category_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_cats, pattern=r"^nf:add_item$")],
    states={
        OrderStates.NONFOOD_CHOOSING_CAT: [
            CallbackQueryHandler(show_items, pattern=r"^nfcat:"),
        ],
        OrderStates.NONFOOD_CHOOSING_ITEM: [
            CallbackQueryHandler(ask_qty, pattern=r"^nfitem:(?!back$)"),
            CallbackQueryHandler(show_cats, pattern=r"^nfitem:back$"),
        ],
        OrderStates.NONFOOD_ENTERING_QTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.NONFOOD_EDITING,
    },
    fallbacks=[],
)
