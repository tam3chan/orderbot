"""Template handlers — ENTERING_TEMPLATE_NAME state."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from states import OrderStates


async def show_template_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Show template save options."""
    from data import list_templates, save_template

    q = update.callback_query
    await q.answer()

    tmpls = list_templates()
    if tmpls:
        btns = [[InlineKeyboardButton(
            f"📋 Ghi đè: {t['name']}",
            callback_data=f"tpl_ow:{t['_id']}")] for t in tmpls]
        btns.append([InlineKeyboardButton("✨ Tạo mẫu mới", callback_data="tpl_new")])
        btns.append([InlineKeyboardButton("↩️ Huỷ", callback_data="tpl_cancel")])
        await q.message.reply_text("💾 *Lưu mẫu:*",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown")
        return OrderStates.ENTERING_TEMPLATE_NAME

    # No existing templates
    ctx.user_data["tpl_action"] = "new"
    await q.message.reply_text("💾 Nhập tên mẫu (VD: *Đơn thường*):",
        parse_mode="Markdown")
    return OrderStates.ENTERING_TEMPLATE_NAME


async def handle_tpl_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle tpl_* callbacks."""
    from data import save_template

    q = update.callback_query
    await q.answer()
    v = q.data

    if v == "tpl_cancel":
        from handlers.conversation.editing import show_edit_screen
        await show_edit_screen(update, ctx)
        return ConversationHandler.END

    if v == "tpl_new":
        ctx.user_data["tpl_action"] = "new"
        await q.message.reply_text("✨ Nhập tên mẫu mới:")
        return OrderStates.ENTERING_TEMPLATE_NAME

    if v.startswith("tpl_ow:"):
        name = v.replace("tpl_ow:", "")
        save_template(name, list(ctx.user_data["order"].values()))
        await q.message.reply_text(f"✅ Đã cập nhật mẫu *{name}*!",
            parse_mode="Markdown")
        from handlers.conversation.editing import show_edit_screen
        return await show_edit_screen(update, ctx)

    return OrderStates.ENTERING_TEMPLATE_NAME


async def receive_tpl_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle template name input."""
    from data import save_template

    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("⚠️ Tên không được để trống:")
        return OrderStates.ENTERING_TEMPLATE_NAME

    save_template(name, list(ctx.user_data["order"].values()))
    await update.message.reply_text(f"✅ Đã lưu mẫu *{name}*!",
        parse_mode="Markdown")
    from handlers.conversation.editing import show_edit_screen
    return await show_edit_screen(update, ctx)


# Nested ConversationHandler for template save flow
template_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_template_menu, pattern=r"^save_tpl_btn$")],
    states={
        OrderStates.ENTERING_TEMPLATE_NAME: [
            CallbackQueryHandler(handle_tpl_action, pattern=r"^tpl_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tpl_name),
        ],
    },
    map_to_parent={
        ConversationHandler.END: OrderStates.EDITING,
    },
    fallbacks=[],
)
