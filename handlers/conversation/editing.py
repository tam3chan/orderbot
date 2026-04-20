"""Editing handlers — EDITING, EDITING_ITEM, ENTERING_EDIT_QTY states."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if q == int(q) else str(q)


async def show_edit_screen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the main order edit screen."""
    order = ctx.user_data.get("order", {})
    btns = []
    for code, item in order.items():
        lbl = f"{item['name']}: {_fmt_qty(item['qty'])} {item['unit']}"
        if len(lbl) > 38:
            lbl = lbl[:35] + "..."
        btns.append([InlineKeyboardButton(f"✏️ {lbl}", callback_data=f"ei:{code}")])

    btns.append([InlineKeyboardButton("➕ Thêm mặt hàng", callback_data="add_item")])
    btns.append([
        InlineKeyboardButton("✅ Xong – Xác nhận", callback_data="done_editing"),
        InlineKeyboardButton("💾 Lưu mẫu", callback_data="save_tpl_btn"),
    ])

    text = f"✏️ *Đơn hàng ({len(order)} món)* — Chạm để sửa:"
    markup = InlineKeyboardMarkup(btns)

    msg = getattr(update, "message", None) or update.callback_query.message
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        await msg.reply_text(text, reply_markup=markup, parse_mode="Markdown")

    return OrderStates.EDITING


async def edit_item_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show quantity editing options for a specific item."""
    q = update.callback_query
    await q.answer()

    code = q.data.replace("ei:", "")
    item = ctx.user_data["order"].get(code)
    if not item:
        return await show_edit_screen(update, ctx)

    ctx.user_data["editing_code"] = code

    btns = [
        [InlineKeyboardButton(str(i), callback_data=f"eq:{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"eq:{i}") for i in range(6, 11)],
        [
            InlineKeyboardButton("✏️ Nhập số khác", callback_data="eq:custom"),
            InlineKeyboardButton("🗑️ Xoá món này", callback_data="eq:remove"),
        ],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="eq:back")],
    ]

    await q.message.edit_text(
        f"✏️ *{item['name']}* ({item['unit']})\n"
        f"Hiện tại: *{_fmt_qty(item['qty'])}*\n"
        "Chọn số lượng mới:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown")

    return OrderStates.EDITING_ITEM


async def handle_item_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle eq:* callbacks in EDITING_ITEM state."""
    q = update.callback_query
    await q.answer()
    v = q.data.replace("eq:", "")
    code = ctx.user_data.get("editing_code")

    if v == "back":
        return await show_edit_screen(update, ctx)

    if v == "remove":
        ctx.user_data["order"].pop(code, None)
        return await show_edit_screen(update, ctx)

    if v == "custom":
        item = ctx.user_data["order"].get(code, {})
        ctx.user_data["editing_code"] = code
        await q.message.edit_text(
            f"✏️ Nhập số lượng cho *{item.get('name', '')}* ({item.get('unit', '')}):\n"
            "(gõ `0` để xoá)",
            parse_mode="Markdown")
        return OrderStates.ENTERING_EDIT_QTY

    try:
        qty = float(v)
        if code and code in ctx.user_data["order"]:
            ctx.user_data["order"][code]["qty"] = qty
    except ValueError:
        pass

    return await show_edit_screen(update, ctx)


async def receive_edit_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom quantity input in ENTERING_EDIT_QTY state."""
    raw = update.message.text.strip().replace(",", ".")
    try:
        qty = float(raw)
    except ValueError:
        await update.message.reply_text("⚠️ Nhập số hợp lệ:")
        return OrderStates.ENTERING_EDIT_QTY

    if qty < 0:
        await update.message.reply_text("⚠️ Không thể âm:")
        return OrderStates.ENTERING_EDIT_QTY

    code = ctx.user_data.get("editing_code")
    if code and code in ctx.user_data["order"]:
        if qty == 0:
            ctx.user_data["order"].pop(code)
        else:
            ctx.user_data["order"][code]["qty"] = qty

    return await show_edit_screen(update, ctx)


async def done_editing(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle done_editing callback — show confirmation screen."""
    from handlers.conversation.confirm import show_confirm_screen

    q = update.callback_query
    await q.answer()

    order = ctx.user_data.get("order", {})
    if not order:
        await q.message.reply_text("🛒 Đơn trống! Thêm mặt hàng trước.")
        return OrderStates.EDITING

    return await show_confirm_screen(update, ctx)
