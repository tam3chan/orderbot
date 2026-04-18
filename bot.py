"""
Telegram Order Bot - Tạo file đặt hàng từ danh sách mặt hàng
"""
import os
import sys
import logging
import io
import functools
from datetime import date
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
)
from openpyxl import load_workbook

# ─── LOGGING ───────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file nếu có (chạy local). Trên server dùng env var thật.
load_dotenv()

# ─── CONFIG ────────────────────────────────────────────────────────────
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.critical("BOT_TOKEN environment variable is required! Set it and restart.")
    sys.exit(1)

EXCEL_PATH = os.environ.get("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")

# Whitelist user IDs (comma-separated). Để trống = không giới hạn (không khuyến khích).
_raw_ids = os.environ.get("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = {int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()}

# ─── EXCEL COLUMN CONSTANTS ────────────────────────────────────────────
# Sheet "Food T01" — 0-indexed
class _Src:
    CAT  = 1
    SUB  = 2
    CODE = 3
    NAME = 4
    NCC  = 9
    UNIT = 20

# Sheet "PR NOODLE" — 1-indexed (openpyxl)
class _Out:
    DATE_ROW   = 4
    DATE_COL   = 12
    ITEM_START = 18   # Hàng đầu tiên ghi sản phẩm
    STT        = 1
    MA_SP      = 2
    TEN_HANG   = 3
    SO_LUONG   = 7
    DVT        = 9
    NGAY_GIAO  = 10
    NCC        = 15

SHEET_SOURCE = "Food T01"
SHEET_OUTPUT = "PR NOODLE"

# ─── STATES ─────────────────────────────────────────────────────────────
CHOOSING_CAT, CHOOSING_ITEM, ENTERING_QTY, CONFIRM_ORDER = range(4)

# ─── AUTHORIZATION DECORATOR ────────────────────────────────────────────
def authorized_only(func):
    """Chặn user không có trong ALLOWED_USER_IDS (nếu whitelist được cấu hình)."""
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            msg = update.effective_message
            if msg:
                await msg.reply_text("⛔ Bạn không có quyền sử dụng bot này.")
            logger.warning("Unauthorized access attempt by user_id=%s", user_id)
            return
        return await func(update, ctx)
    return wrapper

# ─── HELPERS ────────────────────────────────────────────────────────────
def fmt_qty(qty: float) -> str:
    """Hiển thị số lượng: bỏ .0 nếu là số nguyên (2.0 → '2', 2.5 → '2.5')."""
    return str(int(qty)) if qty == int(qty) else str(qty)

# ─── LOAD ITEMS ─────────────────────────────────────────────────────────
def load_food_items() -> dict[str, dict]:
    """Load all food items from Excel. Crash with clear message if file/sheet missing."""
    if not os.path.exists(EXCEL_PATH):
        logger.critical("Excel file not found: %s", EXCEL_PATH)
        sys.exit(1)

    try:
        wb = load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    except Exception as exc:
        logger.critical("Cannot open Excel file '%s': %s", EXCEL_PATH, exc)
        sys.exit(1)

    if SHEET_SOURCE not in wb.sheetnames:
        logger.critical("Sheet '%s' not found. Available: %s", SHEET_SOURCE, wb.sheetnames)
        sys.exit(1)

    ws = wb[SHEET_SOURCE]
    items: dict[str, dict] = {}

    for row in ws.iter_rows(min_row=3, values_only=True):
        code = row[_Src.CODE]
        name = row[_Src.NAME]
        unit = row[_Src.UNIT]
        cat  = row[_Src.CAT]
        sub  = row[_Src.SUB]
        ncc  = row[_Src.NCC]
        if code and name and str(name) != "TÊN SẢN PHẨM":
            items[str(code)] = {
                "code": code,
                "name": str(name),
                "unit": str(unit) if unit else "kg",
                "cat":  str(cat)  if cat  else "Khác",
                "sub":  str(sub)  if sub  else "",
                "ncc":  str(ncc)  if ncc  else "",
            }
    wb.close()
    logger.info("Loaded %d items from '%s'", len(items), EXCEL_PATH)
    return items


def get_categories(items: dict[str, dict]) -> dict[str, list]:
    cats: dict[str, list] = {}
    for v in items.values():
        cats.setdefault(v["cat"], []).append(v)
    return cats


ITEMS = load_food_items()
CATS  = get_categories(ITEMS)

# ─── BUILD EXCEL ORDER FILE ─────────────────────────────────────────────
def build_order_excel(order_items: list[dict], order_date: date | None = None) -> io.BytesIO:
    """
    Điền sản phẩm vào sheet PR NOODLE của template Excel.
    order_items: list of {code, name, qty, unit, ncc}
    Returns BytesIO của file xlsx.
    """
    if order_date is None:
        order_date = date.today()

    wb = load_workbook(EXCEL_PATH)

    if SHEET_OUTPUT not in wb.sheetnames:
        raise ValueError(f"Sheet '{SHEET_OUTPUT}' not found in Excel template.")

    ws = wb[SHEET_OUTPUT]
    ws.cell(row=_Out.DATE_ROW, column=_Out.DATE_COL, value=order_date)

    for i, item in enumerate(order_items):
        r = _Out.ITEM_START + i
        ws.cell(row=r, column=_Out.STT,       value=i + 1)
        ws.cell(row=r, column=_Out.MA_SP,     value=item["code"])
        ws.cell(row=r, column=_Out.TEN_HANG,  value=item["name"])
        ws.cell(row=r, column=_Out.SO_LUONG,  value=item["qty"])
        ws.cell(row=r, column=_Out.DVT,       value=item["unit"])
        ws.cell(row=r, column=_Out.NGAY_GIAO, value=order_date.strftime("%d/%m/%Y"))
        ws.cell(row=r, column=_Out.NCC,       value=item["ncc"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ─── COMMANDS ───────────────────────────────────────────────────────────
@authorized_only
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    text = (
        "👋 Xin chào! Tôi là *Order Bot* 🤖\n\n"
        "Tôi giúp bạn tạo file đặt hàng thực phẩm nhanh chóng.\n\n"
        "📋 *Lệnh có sẵn:*\n"
        "/order — Tạo đơn đặt hàng mới\n"
        "/list — Xem danh sách mặt hàng\n"
        "/tim <từ khoá> — Tìm kiếm mặt hàng\n"
        "/cancel — Huỷ đơn đang làm\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@authorized_only
async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Hiển thị danh sách mặt hàng, tự phân trang nếu vượt giới hạn Telegram."""
    MAX_LEN = 3800  # Telegram limit 4096, chừa buffer

    header = f"📦 *Danh sách mặt hàng ({len(ITEMS)} sản phẩm):*"
    chunks: list[str] = [header]
    current: list[str] = []

    def flush():
        nonlocal current
        if current:
            chunks.append("\n".join(current))
            current = []

    page: list[str] = []
    for cat, items in CATS.items():
        block = [f"\n*{cat}* ({len(items)} món):"]
        for it in items[:5]:
            block.append(f"  • `{it['code']}` {it['name']} ({it['unit']})")
        if len(items) > 5:
            block.append(f"  _...và {len(items)-5} món khác_")

        candidate = "\n".join(page + block)
        if len(candidate) > MAX_LEN:
            flush()
            await update.message.reply_text("\n".join(chunks), parse_mode="Markdown")
            chunks = []
            page = block
        else:
            page.extend(block)

    if page:
        chunks.extend(page)
    if chunks:
        await update.message.reply_text("\n".join(chunks), parse_mode="Markdown")

# ─── ORDER FLOW ─────────────────────────────────────────────────────────
@authorized_only
async def cmd_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"] = {}
    return await show_categories(update, ctx)


async def show_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    btns = [
        [InlineKeyboardButton(f"📁 {cat} ({len(CATS[cat])})", callback_data=f"cat:{cat}")]
        for cat in CATS
    ]
    btns.append([InlineKeyboardButton("✅ Xong – Tạo file đặt hàng", callback_data="done")])

    order = ctx.user_data.get("order", {})
    summary = ""
    if order:
        summary = f"\n\n🛒 *Đơn hiện tại ({len(order)} mặt hàng):*\n"
        for v in order.values():
            summary += f"  • {v['name']}: {fmt_qty(v['qty'])} {v['unit']}\n"

    text   = "📋 Chọn nhóm hàng:" + summary
    markup = InlineKeyboardMarkup(btns)

    msg = update.message or update.callback_query.message
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except BadRequest:
        # Message quá cũ hoặc không edit được
        await msg.reply_text(text, reply_markup=markup, parse_mode="Markdown")

    return CHOOSING_CAT


async def show_items(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("cat:", "")
    ctx.user_data["current_cat"] = cat

    items = CATS.get(cat, [])
    btns = []
    for it in items:
        label = f"{it['name']} ({it['unit']})"
        if len(label) > 40:
            label = label[:37] + "..."
        btns.append([InlineKeyboardButton(label, callback_data=f"item:{it['code']}")])
    btns.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="back_cat")])

    await query.message.edit_text(
        f"📁 *{cat}*\nChọn mặt hàng:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown",
    )
    return CHOOSING_ITEM


async def ask_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.replace("item:", "")
    item = ITEMS.get(code)
    if not item:
        await query.answer("Không tìm thấy mặt hàng!", show_alert=True)
        return CHOOSING_ITEM

    ctx.user_data["current_item"] = item

    existing = ctx.user_data["order"].get(code, {}).get("qty")
    hint = f" (hiện tại: {fmt_qty(existing)})" if existing is not None else ""

    await query.message.reply_text(
        f"✏️ Nhập số lượng cho:\n*{item['name']}* ({item['unit']}){hint}\n\n"
        f"Nhập số lượng hoặc gõ `0` để bỏ:",
        parse_mode="Markdown",
    )
    return ENTERING_QTY


async def receive_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        qty = float(text)
    except ValueError:
        await update.message.reply_text("⚠️ Vui lòng nhập số hợp lệ (VD: 5, 2.5)")
        return ENTERING_QTY

    # Validate: không cho phép số âm
    if qty < 0:
        await update.message.reply_text("⚠️ Số lượng không thể âm. Nhập lại (hoặc `0` để bỏ):", parse_mode="Markdown")
        return ENTERING_QTY

    item = ctx.user_data.get("current_item")
    if not item:
        await update.message.reply_text("❌ Lỗi phiên. Gõ /order để bắt đầu lại.")
        return ConversationHandler.END

    code = str(item["code"])
    if qty == 0:
        ctx.user_data["order"].pop(code, None)
        await update.message.reply_text(f"🗑️ Đã xoá *{item['name']}* khỏi đơn.", parse_mode="Markdown")
    else:
        ctx.user_data["order"][code] = {
            "code": item["code"],
            "name": item["name"],
            "qty":  qty,
            "unit": item["unit"],
            "ncc":  item["ncc"],
        }
        await update.message.reply_text(
            f"✅ *{item['name']}*: {fmt_qty(qty)} {item['unit']}", parse_mode="Markdown"
        )

    return await show_categories(update, ctx)


async def back_to_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await show_categories(update, ctx)


async def done_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order = ctx.user_data.get("order", {})
    if not order:
        await query.message.reply_text("🛒 Đơn hàng trống! Thêm mặt hàng trước.")
        return CHOOSING_CAT

    lines = ["📋 *Xác nhận đơn đặt hàng:*\n"]
    for v in order.values():
        lines.append(f"  • {v['name']}: *{fmt_qty(v['qty'])} {v['unit']}*")
    lines.append(f"\n_Tổng: {len(order)} mặt hàng_")

    btns = [[
        InlineKeyboardButton("✅ Tạo file Excel", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Huỷ",            callback_data="confirm_no"),
    ]]
    await query.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown",
    )
    return CONFIRM_ORDER


async def confirm_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Đang tạo file...")

    order = ctx.user_data.get("order", {})
    items_list = list(order.values())

    try:
        buf = build_order_excel(items_list)
        today = date.today()
        filename = f"DonDatHang_{today.strftime('%d%m%Y')}.xlsx"
        await query.message.reply_document(
            document=buf,
            filename=filename,
            caption=(
                f"✅ *File đặt hàng ngày {today.strftime('%d/%m/%Y')}*\n"
                f"📦 {len(items_list)} mặt hàng\n\n"
                f"_Gửi file này cho nhà cung cấp!_"
            ),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Error building order file")
        await query.message.reply_text("❌ Lỗi tạo file. Vui lòng thử lại hoặc liên hệ admin.")

    ctx.user_data.clear()
    return ConversationHandler.END


async def confirm_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ Đã huỷ. Gõ /order để bắt đầu lại.")
    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Đã huỷ đơn hàng. Gõ /order để bắt đầu lại.")
    return ConversationHandler.END

# ─── SEARCH: /tim <keyword> ─────────────────────────────────────────────
@authorized_only
async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Cú pháp: /tim <từ khoá>\nVD: /tim thịt bò")
        return
    kw = " ".join(ctx.args).lower()
    found = [v for v in ITEMS.values() if kw in v["name"].lower()]
    if not found:
        await update.message.reply_text(f"❌ Không tìm thấy '{kw}'")
        return
    lines = [f"🔍 *Kết quả tìm kiếm '{kw}':*\n"]
    for it in found[:20]:
        lines.append(f"  `{it['code']}` {it['name']} ({it['unit']}) — {it['ncc']}")
    if len(found) > 20:
        lines.append(f"\n_...và {len(found)-20} kết quả khác_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── MAIN ───────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("order", cmd_order)],
        states={
            CHOOSING_CAT: [
                CallbackQueryHandler(show_items,  pattern="^cat:"),
                CallbackQueryHandler(done_order,  pattern="^done$"),
            ],
            CHOOSING_ITEM: [
                CallbackQueryHandler(ask_qty,     pattern="^item:"),
                CallbackQueryHandler(back_to_cat, pattern="^back_cat$"),
            ],
            ENTERING_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_yes, pattern="^confirm_yes$"),
                CallbackQueryHandler(confirm_no,  pattern="^confirm_no$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("tim",    cmd_search))
    app.add_handler(conv)

    logger.info("Bot đang chạy... (%d items loaded)", len(ITEMS))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
