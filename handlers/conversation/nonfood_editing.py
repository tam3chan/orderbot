"""Non-food editing screen, item keypad, and top-level non-food ConversationHandler.

Wires together:
- nonfood_entry entry/history handlers
- nonfood_category_conv (category browse nested handler)
- nonfood_search_conv (exact-code search nested handler)

Returns NONFOOD_EDITING as the central hub state.
"""
from typing import Any, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


# ─── Imports from nonfood_entry (entry/history flow) ───────────────────────────

from handlers.conversation.nonfood_entry import (  # noqa: E402
    NONFOOD_SESSION_KEYS,
    cmd_order_nonfood,
    handle_nonfood_entry,
    handle_nonfood_history_entry,
    receive_nonfood_history_date,
)


# ─── Import from nonfood_category (shared edit screen + nested handler) ───────

from handlers.conversation.nonfood_category import (  # noqa: E402
    _show_nonfood_edit_screen,
    nonfood_category_conv,
)


# ─── Import from nonfood_search (nested search handler) ─────────────────────────

from handlers.conversation.nonfood_search import nonfood_search_conv  # noqa: E402


# ─── Import from nonfood_template (save/load handlers) ──────────────────────────

from handlers.conversation.nonfood_template import (  # noqa: E402
    handle_nonfood_template,
    receive_nonfood_template_name,
    show_nonfood_template_menu,
)


# ─── Import from nonfood_confirm (confirm/export handlers) ────────────────────────

from handlers.conversation.nonfood_confirm import (  # noqa: E402
    handle_nonfood_date_choice,
    receive_nonfood_confirm,
    receive_nonfood_date,
    show_nonfood_confirm_screen,
)


# ─── Edit menu handler (NONFOOD_EDITING state) ──────────────────────────────────


async def handle_nonfood_edit_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Route nfei:edit:{code} → item keypad; nfe:confirm → done; nfe:save → save."""
    q = update.callback_query
    await q.answer()
    raw = q.data or ""

    if raw.startswith("nfei:edit:"):
        code = raw.replace("nfei:edit:", "", 1)
        return await _show_nonfood_item_keypad(update, ctx, code)

    if raw == "nfe:confirm":
        return await _nonfood_done_editing(update, ctx)

    if raw == "nfe:save":
        return await show_nonfood_template_menu(update, ctx)

    # Fallback: redisplay edit screen
    return await _show_nonfood_edit_screen(update, ctx)


async def _show_nonfood_item_keypad(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, code: str
) -> int:
    """Show qty keypad for a non-food item being edited."""
    q = update.callback_query
    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    item = nonfood_order.get(code)

    if not item:
        await q.answer("Món không còn trong đơn!", show_alert=True)
        return OrderStates.NONFOOD_EDITING

    ctx.user_data["nf_editing_code"] = code

    btns = [
        [InlineKeyboardButton(str(i), callback_data=f"nfeq:{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"nfeq:{i}") for i in range(6, 11)],
        [
            InlineKeyboardButton("✏️ Nhập số khác", callback_data="nfeq:custom"),
            InlineKeyboardButton("🗑️ Xoá món này", callback_data="nfeq:remove"),
        ],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="nfeq:back")],
    ]

    source_note = f" [{item.get('source', '')}]" if item.get("source") else ""
    await q.message.edit_text(
        f"✏️ *{item['name']}* ({item['unit']}){source_note}\n"
        f"Hiện tại: *{_fmt_qty(item['qty'])}*\n"
        "Chọn số lượng mới:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown",
    )
    return OrderStates.NONFOOD_EDITING_ITEM


async def _nonfood_done_editing(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle nfe:confirm — show confirm screen."""
    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    if not nonfood_order:
        message = update.callback_query.message
        await message.reply_text("🛒 Đơn trống! Thêm mặt hàng trước.")
        return OrderStates.NONFOOD_EDITING

    return await show_nonfood_confirm_screen(update, ctx)


# ─── Qty keypad handler (NONFOOD_EDITING_ITEM state) ─────────────────────────


async def handle_nonfood_edit_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle nfeq: preset / remove / custom / back in NONFOOD_EDITING_ITEM."""
    q = update.callback_query
    await q.answer()
    raw = q.data or ""
    v = raw.replace("nfeq:", "")
    code = cast(str, ctx.user_data.get("nf_editing_code"))

    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))

    if v == "back":
        return await _show_nonfood_edit_screen(update, ctx)

    if v == "remove":
        nonfood_order.pop(code, None)
        return await _show_nonfood_edit_screen(update, ctx)

    if v == "custom":
        item = nonfood_order.get(code, {})
        await q.message.edit_text(
            f"✏️ Nhập số lượng cho *{item.get('name', '')}* ({item.get('unit', '')}):\n"
            "(gõ `0` để xoá)",
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_EDIT_QTY

    # Preset qty button (1-10)
    try:
        qty = float(v)
        if code in nonfood_order:
            nonfood_order[code]["qty"] = qty
    except ValueError:
        pass

    return await _show_nonfood_edit_screen(update, ctx)


# ─── Custom qty input handler (NONFOOD_ENTERING_EDIT_QTY state) ─────────────


async def receive_nonfood_edit_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom qty input in NONFOOD_ENTERING_EDIT_QTY state."""
    message = update.message
    assert message is not None

    raw = message.text.strip().replace(",", ".")
    try:
        qty = float(raw)
    except ValueError:
        await message.reply_text("⚠️ Nhập số hợp lệ:")
        return OrderStates.NONFOOD_ENTERING_EDIT_QTY

    if qty < 0:
        await message.reply_text("⚠️ Không thể âm:")
        return OrderStates.NONFOOD_ENTERING_EDIT_QTY

    code = cast(str, ctx.user_data.get("nf_editing_code"))
    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))

    if code in nonfood_order:
        if qty == 0:
            nonfood_order.pop(code, None)
        else:
            nonfood_order[code]["qty"] = qty

    return await _show_nonfood_edit_screen(update, ctx)


# ─── Cancel ───────────────────────────────────────────────────────────────────


async def cmd_cancel_nonfood(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the non-food session and clean up."""
    user_data = cast(dict[str, Any], ctx.user_data)
    for key in NONFOOD_SESSION_KEYS:
        user_data.pop(key, None)

    message = update.message
    assert message is not None
    await message.reply_text("❌ Đã huỷ đơn non-food. Gõ /order_nonfood để bắt đầu lại.")
    return ConversationHandler.END


# ─── Top-level non-food ConversationHandler ───────────────────────────────────


nonfood_conv = ConversationHandler(
    entry_points=[
        # Re-entry: any nfe:* callback from editing screen goes to edit menu handler
        CallbackQueryHandler(handle_nonfood_edit_menu, pattern=r"^nfe:"),
    ],
    states={
        # From /order_nonfood entry point
        OrderStates.NONFOOD_ENTRY_POINT: [
            CallbackQueryHandler(handle_nonfood_entry, pattern=r"^nfe:"),
        ],
        # History browsing
        OrderStates.NONFOOD_CHOOSING_HISTORY: [
            CallbackQueryHandler(handle_nonfood_history_entry, pattern=r"^nfh:"),
        ],
        OrderStates.NONFOOD_ENTERING_HISTORY_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nonfood_history_date),
        ],
        # Central editing hub + nested browse/search
        OrderStates.NONFOOD_EDITING: [
            CallbackQueryHandler(handle_nonfood_edit_menu, pattern=r"^nfe"),
            nonfood_category_conv,   # handles nf:add_item → category browse
            nonfood_search_conv,    # handles nfsearch: → exact code search
        ],
        # Item qty keypad
        OrderStates.NONFOOD_EDITING_ITEM: [
            CallbackQueryHandler(handle_nonfood_edit_qty, pattern=r"^nfeq:"),
        ],
        # Custom qty input
        OrderStates.NONFOOD_ENTERING_EDIT_QTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nonfood_edit_qty),
        ],
        # Forward refs (Tasks 8-9)
        OrderStates.NONFOOD_CONFIRM_ORDER: [
            CallbackQueryHandler(receive_nonfood_confirm, pattern=r"^nfeq:"),
        ],
        OrderStates.NONFOOD_ENTERING_DATE: [
            CallbackQueryHandler(handle_nonfood_date_choice, pattern=r"^nfqdate:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nonfood_date),
        ],
        OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME: [
            CallbackQueryHandler(handle_nonfood_template, pattern=r"^nftpl:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nonfood_template_name),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cmd_cancel_nonfood),
    ],
)
