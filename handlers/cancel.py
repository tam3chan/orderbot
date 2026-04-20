"""Cancel command handler."""
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command - clear user data and end conversation."""
    ctx.user_data.clear()
    await update.message.reply_text("❌ Đã huỷ. Gõ /order để bắt đầu lại.")
    return ConversationHandler.END
