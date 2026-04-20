"""Telegram Order Bot v2 — Pure wiring, all logic in handlers."""
import os, sys, logging, io, functools
from dotenv import load_dotenv

import data, data.r2_storage
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler,
)

from states import OrderStates
from services.excel_service import ExcelService
from services.order_service import OrderService
from handlers import cmd_start, cmd_list, cmd_search, cmd_cancel
from handlers.conversation.entry import cmd_order, handle_entry, handle_history_entry, receive_history_date
from handlers.conversation.editing import show_edit_screen, edit_item_menu, handle_item_edit, receive_edit_qty
from handlers.conversation.category import category_conv, show_cats
from handlers.conversation.confirm import confirm_yes, confirm_no, back_to_edit, change_date, quick_date, enter_custom_date, show_confirm_screen
from handlers.conversation.template import template_conv, show_template_menu

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.critical("BOT_TOKEN required"); sys.exit(1)
EXCEL_PATH = os.environ.get("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")
_raw = os.environ.get("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = {int(x.strip()) for x in _raw.split(",") if x.strip()}

EXCEL_BUFFER: io.BytesIO | None = None

def _init_excel_buffer() -> None:
    global EXCEL_BUFFER
    if os.environ.get("R2_ENDPOINT") and os.environ.get("R2_ACCESS_KEY"):
        EXCEL_BUFFER = data.r2_storage.download_excel()
    else:
        logger.info("R2 not configured, using local Excel file: %s", EXCEL_PATH)

def authorized_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, ctx):
        uid = update.effective_user.id if update.effective_user else None
        if ALLOWED_USER_IDS and uid not in ALLOWED_USER_IDS:
            m = update.effective_message
            if m: await m.reply_text("⛔ Không có quyền.")
            return
        return await func(update, ctx)
    return wrapper


async def done_editing_forward(update, ctx):
    from handlers.conversation.editing import done_editing
    return await done_editing(update, ctx)


def main():
    _init_excel_buffer()
    excel_service = ExcelService(buffer=EXCEL_BUFFER, local_path=EXCEL_PATH)
    ITEMS, CATS = excel_service.load_items()

    app = Application.builder().token(TOKEN).build()
    app.bot_data["excel_buffer"] = EXCEL_BUFFER
    app.bot_data["excel_service"] = excel_service
    app.bot_data["order_service"] = OrderService(db=data, excel_service=excel_service)
    app.bot_data["items"] = ITEMS
    app.bot_data["categories"] = CATS

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("tim", cmd_search))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("order", cmd_order)],
        states={
            OrderStates.ENTRY_POINT: [CallbackQueryHandler(handle_entry, pattern=r"^en:")],
            OrderStates.CHOOSING_HISTORY: [CallbackQueryHandler(handle_history_entry, pattern=r"^hi:")],
            OrderStates.ENTERING_HISTORY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_history_date)],
            OrderStates.EDITING: [
                CallbackQueryHandler(edit_item_menu, pattern=r"^ei:"),
                CallbackQueryHandler(done_editing_forward, pattern=r"^done_editing$"),
                CallbackQueryHandler(show_template_menu, pattern=r"^save_tpl_btn$"),
                category_conv, template_conv,
            ],
            OrderStates.EDITING_ITEM: [CallbackQueryHandler(handle_item_edit, pattern=r"^eq:")],
            OrderStates.ENTERING_EDIT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_qty)],
            OrderStates.CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_yes, pattern=r"^confirm_yes$"),
                CallbackQueryHandler(confirm_no, pattern=r"^confirm_no$"),
                CallbackQueryHandler(back_to_edit, pattern=r"^back_to_edit$"),
                CallbackQueryHandler(change_date, pattern=r"^change_date$"),
                CallbackQueryHandler(quick_date, pattern=r"^qdate:"),
            ],
            OrderStates.ENTERING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_date)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    ))

    logger.info("Bot đang chạy... (%d items loaded)", len(ITEMS))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
