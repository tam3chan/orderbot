"""Telegram Order Bot v2 — Pure wiring, all logic in handlers."""
import os, sys, logging, io, functools
from dotenv import load_dotenv

import data, data.r2_storage
from telegram import Update, BotCommand
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
from handlers.conversation.nonfood_editing import nonfood_conv

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.critical("BOT_TOKEN required"); sys.exit(1)
EXCEL_PATH = os.environ.get("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")
NONFOOD_EXCEL_PATH = "ORDER NONFOOD MIN xlsx.xlsx"
_raw = os.environ.get("ALLOWED_USER_IDS", "")
try:
    ALLOWED_USER_IDS: set[int] = {int(x.strip()) for x in _raw.split(",") if x.strip()}
except ValueError as e:
    logger.critical("ALLOWED_USER_IDS contains invalid integer: %s", e)
    sys.exit(1)

EXCEL_BUFFER: io.BytesIO | None = None


def fmt_qty(q: float) -> str:
    """Format quantity for legacy utility tests and display helpers."""
    return str(int(q)) if q == int(q) else str(q)


def get_categories(items: dict) -> dict:
    """Group loaded item dictionaries by their category key."""
    categories: dict = {}
    for item in items.values():
        categories.setdefault(item["cat"], []).append(item)
    return categories


def _init_excel_buffer() -> None:
    global EXCEL_BUFFER
    if os.environ.get("R2_ENDPOINT") and os.environ.get("R2_ACCESS_KEY"):
        EXCEL_BUFFER = data.r2_storage.download_excel()
    else:
        logger.info("R2 not configured, using local Excel file: %s", EXCEL_PATH)


async def post_init(app) -> None:
    commands = [
        BotCommand("order", "Tạo đơn đặt hàng"),
        BotCommand("list", "Xem danh sách mặt hàng"),
        BotCommand("tim", "Tìm kiếm mặt hàng"),
        BotCommand("cancel", "Huỷ thao tác hiện tại"),
    ]
    if app.bot_data.get("nonfood_enabled"):
        commands.insert(1, BotCommand("order_nonfood", "Tạo đơn non-food"))
    await app.bot.set_my_commands(commands)


def _bootstrap_nonfood_assets(
    service_cls: type[ExcelService] = ExcelService,
    download_excel_fn=None,
) -> dict[str, object]:
    """Bootstrap non-food workbook assets without affecting food startup."""
    if download_excel_fn is None:
        download_excel_fn = data.r2_storage.download_excel

    r2_configured = all(os.environ.get(k) for k in ("R2_ENDPOINT", "R2_ACCESS_KEY", "R2_SECRET_KEY"))
    nonfood_key = os.environ.get("NONFOOD_R2_OBJECT_KEY")
    nonfood_path = os.environ.get("NONFOOD_EXCEL_PATH") or NONFOOD_EXCEL_PATH

    assets: dict[str, object] = {
        "nonfood_enabled": False,
        "nonfood_excel_buffer": None,
        "nonfood_excel_service": None,
        "nonfood_items": {},
        "nonfood_categories": {},
        "nonfood_order_service": None,
    }

    nonfood_service = None
    nonfood_items = {}
    nonfood_categories = {}

    # Try R2 first
    if r2_configured and nonfood_key:
        try:
            nonfood_buffer = download_excel_fn(object_key=nonfood_key)
            nonfood_service = service_cls(buffer=nonfood_buffer)
            assets["nonfood_excel_buffer"] = nonfood_buffer
        except Exception as e:
            nonfood_service = None
            logger.warning("R2 download failed for non-food workbook (%s); trying local path", e)

    # Fall back to local path if R2 not available or failed
    if nonfood_service is None:
        try:
            nonfood_service = service_cls(local_path=nonfood_path)
        except Exception:
            logger.exception("Non-food workbook bootstrap failed; disabling non-food flow")
            return assets

    # Load items
    try:
        nonfood_items, nonfood_categories = nonfood_service.load_items_nonfood()
    except Exception:
        logger.exception("Non-food workbook bootstrap failed; disabling non-food flow")
        return assets

    assets["nonfood_enabled"] = True
    assets["nonfood_excel_service"] = nonfood_service
    assets["nonfood_items"] = nonfood_items
    assets["nonfood_categories"] = nonfood_categories
    assets["nonfood_order_service"] = OrderService(db=data, excel_service=nonfood_service)
    return assets


def _build_bot_data(excel_service: ExcelService, items: dict, categories: dict) -> dict[str, object]:
    """Build the shared bot_data contract for food and non-food assets."""
    bot_data: dict[str, object] = {
        "excel_buffer": EXCEL_BUFFER,
        "excel_service": excel_service,
        "order_service": OrderService(db=data, excel_service=excel_service),
        "items": items,
        "categories": categories,
    }
    bot_data.update(_bootstrap_nonfood_assets())
    return bot_data

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

    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.bot_data.update(_build_bot_data(excel_service, ITEMS, CATS))

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
    # Top-level /order_nonfood command (visible in Telegram bot command menu)
    from handlers.conversation.nonfood_editing import cmd_order_nonfood
    app.add_handler(CommandHandler("order_nonfood", cmd_order_nonfood))
    app.add_handler(nonfood_conv)

    logger.info("Bot đang chạy... (%d items loaded)", len(ITEMS))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
