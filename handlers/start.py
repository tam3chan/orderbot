"""Start command handler."""
from telegram import Update
from telegram.ext import ContextTypes
from data import ping_db


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show welcome and connection status."""
    ctx.user_data.clear()

    # R2 status from bot_data
    excel_buf = ctx.bot_data.get("excel_buffer")
    if excel_buf:
        size_kb = round(excel_buf.getbuffer().nbytes / 1024)
        items_count = len(ctx.bot_data.get("items", {}))
        r2_status = f"✅ Đã kết nối ({size_kb} KB, {items_count} mặt hàng)"
    else:
        r2_status = "⚠️ Không dùng R2 (đọc local)"

    # MongoDB status
    mongo_status = "✅ Đã kết nối" if ping_db() else "❌ Không kết nối được"

    await update.message.reply_text(
        f"👋 Xin chào! Tôi là *Order Bot* 🤖\n\n"
        f"🔗 *Trạng thái kết nối:*\n"
        f"  • R2 Storage: {r2_status}\n"
        f"  • MongoDB: {mongo_status}\n\n"
        f"📋 *Lệnh có sẵn:*\n"
        "/order — Tạo đơn đặt hàng\n"
        "/list — Xem danh sách mặt hàng\n"
        "/tim <từ khoá> — Tìm kiếm\n"
        "/cancel — Huỷ",
        parse_mode="Markdown",
    )
