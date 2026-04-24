"""Non-food exact code search handlers — NONFOOD_SEARCHING state."""
from typing import Any, cast

from telegram import Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, filters, MessageHandler

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


async def start_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point from editing screen — ask user to type a code."""
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "🔍 *Nhập mã sản phẩm non-food:*\n"
        "(gõ `back` để quay lại)",
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_SEARCHING


async def ask_search_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE, item: dict) -> int:
    """Ask quantity for a matched search item — sets nf_current_item and prompts."""
    user_data = cast(dict[str, Any], ctx.user_data)
    user_data["nf_current_item"] = item

    code = str(item["code"])
    nonfood_order = cast(dict, user_data.get("nonfood_order", {}))
    existing = nonfood_order.get(code, {}).get("qty")
    hint = f" (hiện: {_fmt_qty(existing)})" if existing is not None else ""

    await update.message.reply_text(
        f"✏️ *{item['name']}* ({item['unit']}){hint}\n"
        "Nhập số lượng (0 = bỏ):",
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_ENTERING_QTY


async def receive_search_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle exact code input in search state."""
    from handlers.conversation.nonfood_category import ask_qty

    message = update.message
    assert message is not None
    raw = message.text.strip()

    if raw.lower() == "back":
        return ConversationHandler.END

    code = str(raw)
    items = cast(dict, ctx.bot_data.get("nonfood_items", {}))
    item = items.get(code)

    if not item:
        await message.reply_text(
            f"❌ Không tìm thấy mã `{code}`. Nhập lại mã:",
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_SEARCHING

    return await ask_search_qty(update, ctx, item)


async def receive_search_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input after a search match."""
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen

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


# Nested ConversationHandler for non-food code search sub-flow
nonfood_search_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_search, pattern=r"^nfsearch:")],
    states={
        OrderStates.NONFOOD_SEARCHING: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_code),
        ],
        OrderStates.NONFOOD_ENTERING_QTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_qty),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.NONFOOD_EDITING,
    },
    fallbacks=[],
)
