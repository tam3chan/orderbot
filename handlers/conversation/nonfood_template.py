"""Non-food template save/load handlers — NONFOOD_ENTERING_TEMPLATE_NAME state."""
from typing import Any, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, filters, MessageHandler

from states import OrderStates


def _fmt_qty(q: float) -> str:
    return str(int(q)) if int(q) == q else str(q)


async def show_nonfood_template_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show existing non-food templates when user clicks nfe:save."""
    from data import list_nonfood_templates

    q = update.callback_query
    await q.answer()

    tmpls = list_nonfood_templates()
    if tmpls:
        btns = [
            [InlineKeyboardButton(f"📋 {t['name']}", callback_data=f"nftpl:{t['_id']}")]
            for t in tmpls
        ]
        btns.append([InlineKeyboardButton("✨ Tạo mẫu mới", callback_data="nftpl:new")])
        btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="nftpl:back")])
        await q.message.reply_text(
            "💾 *Lưu mẫu non-food:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME

    # No existing templates → prompt directly for name
    await q.message.reply_text("💾 Nhập tên mẫu mới (VD: *Đơn văn phòng*):", parse_mode="Markdown")
    return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME


async def handle_nonfood_template(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle nftpl:* callbacks in NONFOOD_ENTERING_TEMPLATE_NAME."""
    from data import get_nonfood_template

    q = update.callback_query
    await q.answer()
    raw = q.data or ""
    user_data = cast(dict[str, Any], ctx.user_data)

    if raw == "nftpl:new":
        await q.message.reply_text("✨ Nhập tên mẫu mới:")
        return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME

    if raw == "nftpl:back":
        from handlers.conversation.nonfood_category import _show_nonfood_edit_screen
        await _show_nonfood_edit_screen(update, ctx)
        return OrderStates.NONFOOD_EDITING

    if raw.startswith("nftpl:overwrite:"):
        template_id = raw.replace("nftpl:overwrite:", "", 1)
        return await _overwrite_nonfood_template(update, ctx, template_id)

    if raw.startswith("nftpl:"):
        template_id = raw.replace("nftpl:", "", 1)
        items = get_nonfood_template(template_id)
        user_data["nonfood_order"] = {str(item["code"]): item for item in (items or [])}
        from handlers.conversation.nonfood_category import _show_nonfood_edit_screen
        await _show_nonfood_edit_screen(update, ctx)
        return OrderStates.NONFOOD_EDITING

    return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME


async def receive_nonfood_template_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle template name input — save new or offer overwrite."""
    from data import list_nonfood_templates, save_nonfood_template

    message = update.message
    assert message is not None
    name = message.text.strip()

    if not name:
        await message.reply_text("⚠️ Tên không được để trống:")
        return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME

    # Check if name matches an existing template
    tmpls = list_nonfood_templates()
    existing = next((t for t in tmpls if t["name"] == name), None)

    if existing:
        user_data = cast(dict[str, Any], ctx.user_data)
        user_data["nf_template_overwrite_id"] = existing["_id"]
        btns = [
            [InlineKeyboardButton(f"⚠️ Ghi đè: {existing['name']}", callback_data=f"nftpl:overwrite:{existing['_id']}")],
            [InlineKeyboardButton("↩️ Quay lại", callback_data="nftpl:back")],
        ]
        await message.reply_text(
            f"📋 Mẫu *{name}* đã tồn tại. Ghi đè?",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown",
        )
        return OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME

    # New template — save directly
    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    save_nonfood_template(
        name,
        [
            {"code": code, "name": item["name"], "qty": item["qty"], "unit": item["unit"], "source": item["source"]}
            for code, item in nonfood_order.items()
        ],
    )
    await message.reply_text(f"✅ Đã lưu mẫu *{name}*!", parse_mode="Markdown")
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen
    return await _show_nonfood_edit_screen(update, ctx)


async def _overwrite_nonfood_template(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, template_id: str
) -> int:
    """Overwrite an existing non-food template."""
    from data import list_nonfood_templates, save_nonfood_template

    q = update.callback_query
    tmpls = list_nonfood_templates()
    template_doc = next((t for t in tmpls if t["_id"] == template_id), None)
    if not template_doc:
        await q.answer("❌ Mẫu không tìm thấy!", show_alert=True)
        return OrderStates.NONFOOD_EDITING

    nonfood_order = cast(dict, ctx.user_data.get("nonfood_order", {}))
    save_nonfood_template(
        template_id,
        [
            {"code": code, "name": item["name"], "qty": item["qty"], "unit": item["unit"], "source": item["source"]}
            for code, item in nonfood_order.items()
        ],
    )
    await q.message.reply_text(f"✅ Đã cập nhật mẫu *{template_doc['name']}*!", parse_mode="Markdown")
    from handlers.conversation.nonfood_category import _show_nonfood_edit_screen
    return await _show_nonfood_edit_screen(update, ctx)
