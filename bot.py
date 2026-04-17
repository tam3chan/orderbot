"""
Telegram Order Bot - Tạo file đặt hàng từ danh sách mặt hàng
"""
import os
import logging
import json
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import io
import shutil

# ─── LOGGING ───────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── CONFIG ────────────────────────────────────────────────────────────
TOKEN = os.environ.get("BOT_TOKEN", "8772576507:AAEcB0YAqSGSRxNqtJ5UTQCkGnLh8YX72Fk")
EXCEL_PATH = os.environ.get("EXCEL_PATH", "DAILY_ORDER_MIN_xlsx.xlsx")

# ─── STATES ─────────────────────────────────────────────────────────────
CHOOSING_CAT, CHOOSING_ITEM, ENTERING_QTY, CONFIRM_ORDER = range(4)

# ─── LOAD ITEMS ─────────────────────────────────────────────────────────
def load_food_items():
    """Load all food items from Excel"""
    wb = load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb["Food T01"]
    items = {}  # code -> dict

    for row in ws.iter_rows(min_row=3, values_only=True):
        code = row[3]   # Mã
        name = row[4]   # TÊN SẢN PHẨM
        unit = row[20]  # Đơn vị
        cat  = row[1]   # CAT
        sub  = row[2]   # Phân loại
        ncc  = row[9]   # NCC
        if code and name and str(name) != "TÊN SẢN PHẨM":
            items[str(code)] = {
                "code": code,
                "name": str(name),
                "unit": str(unit) if unit else "kg",
                "cat":  str(cat) if cat else "Khác",
                "sub":  str(sub) if sub else "",
                "ncc":  str(ncc) if ncc else "",
            }
    wb.close()
    return items

def get_categories(items):
    cats = {}
    for v in items.values():
        cat = v["cat"]
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(v)
    return cats

ITEMS = load_food_items()
CATS  = get_categories(ITEMS)

# ─── HELPER: Build Excel order file ─────────────────────────────────────
def build_order_excel(order_items, order_date=None):
    """
    order_items: list of {code, name, qty, unit, ncc}
    Returns BytesIO with xlsx
    """
    src = EXCEL_PATH
    wb = load_workbook(src)
    ws = wb["PR NOODLE"]

    if order_date is None:
        order_date = date.today()

    # Set date (row 4, col L = 12)
    ws.cell(row=4, column=12, value=order_date)

    # Header rows for items start at row 18
    START_ROW = 18

    for i, item in enumerate(order_items):
        r = START_ROW + i
        ws.cell(row=r, column=1,  value=i + 1)         # STT
        ws.cell(row=r, column=2,  value=item["code"])  # Mã SP
        ws.cell(row=r, column=3,  value=item["name"])  # Tên hàng
        ws.cell(row=r, column=7,  value=item["qty"])   # Số lượng
        ws.cell(row=r, column=9,  value=item["unit"])  # ĐVT
        ws.cell(row=r, column=10, value=order_date.strftime("%d/%m/%Y"))  # Ngày giao
        ws.cell(row=r, column=15, value=item["ncc"])   # NCC

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ─── COMMANDS ───────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    text = (
        "👋 Xin chào! Tôi là *Order Bot* 🤖\n\n"
        "Tôi giúp bạn tạo file đặt hàng thực phẩm nhanh chóng.\n\n"
        "📋 *Lệnh có sẵn:*\n"
        "/order — Tạo đơn đặt hàng mới\n"
        "/list — Xem danh sách mặt hàng\n"
        "/cancel — Huỷ đơn đang làm\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = [f"📦 *Danh sách mặt hàng ({len(ITEMS)} sản phẩm):*\n"]
    for cat, items in CATS.items():
        lines.append(f"\n*{cat}* ({len(items)} món):")
        for it in items[:5]:
            lines.append(f"  • `{it['code']}` {it['name']} ({it['unit']})")
        if len(items) > 5:
            lines.append(f"  _...và {len(items)-5} món khác_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── ORDER FLOW ─────────────────────────────────────────────────────────
async def cmd_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["order"] = {}   # code -> {name, qty, unit, ncc}
    return await show_categories(update, ctx)

async def show_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    btns = []
    for cat in CATS:
        btns.append([InlineKeyboardButton(f"📁 {cat} ({len(CATS[cat])})", callback_data=f"cat:{cat}")])
    btns.append([InlineKeyboardButton("✅ Xong – Tạo file đặt hàng", callback_data="done")])

    order = ctx.user_data.get("order", {})
    summary = ""
    if order:
        summary = f"\n\n🛒 *Đơn hiện tại ({len(order)} mặt hàng):*\n"
        for v in order.values():
            summary += f"  • {v['name']}: {v['qty']} {v['unit']}\n"

    text = "📋 Chọn nhóm hàng:" + summary
    markup = InlineKeyboardMarkup(btns)

    msg = update.message or update.callback_query.message
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
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
        parse_mode="Markdown"
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

    # Check if already in order
    existing = ctx.user_data["order"].get(code, {}).get("qty", "")
    hint = f" (hiện tại: {existing})" if existing else ""

    await query.message.reply_text(
        f"✏️ Nhập số lượng cho:\n*{item['name']}* ({item['unit']}){hint}\n\n"
        f"Nhập số lượng hoặc gõ `0` để bỏ:",
        parse_mode="Markdown"
    )
    return ENTERING_QTY

async def receive_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        qty = float(text)
    except ValueError:
        await update.message.reply_text("⚠️ Vui lòng nhập số hợp lệ (VD: 5, 2.5)")
        return ENTERING_QTY

    item = ctx.user_data.get("current_item")
    if not item:
        await update.message.reply_text("❌ Lỗi. Gõ /order để bắt đầu lại.")
        return ConversationHandler.END

    code = str(item["code"])
    if qty == 0:
        ctx.user_data["order"].pop(code, None)
        await update.message.reply_text(f"🗑️ Đã xoá *{item['name']}* khỏi đơn.", parse_mode="Markdown")
    else:
        ctx.user_data["order"][code] = {
            "code": item["code"],
            "name": item["name"],
            "qty": qty,
            "unit": item["unit"],
            "ncc": item["ncc"],
        }
        await update.message.reply_text(
            f"✅ *{item['name']}*: {qty} {item['unit']}", parse_mode="Markdown"
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

    # Summary
    lines = ["📋 *Xác nhận đơn đặt hàng:*\n"]
    total = 0
    for v in order.values():
        lines.append(f"  • {v['name']}: *{v['qty']} {v['unit']}*")
        total += 1
    lines.append(f"\n_Tổng: {total} mặt hàng_")

    btns = [
        [
            InlineKeyboardButton("✅ Tạo file Excel", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Huỷ", callback_data="confirm_no"),
        ]
    ]
    await query.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="Markdown"
    )
    return CONFIRM_ORDER

async def confirm_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Đang tạo file...")

    order = ctx.user_data.get("order", {})
    items_list = list(order.values())

    try:
        buf = build_order_excel(items_list)
        today = date.today().strftime("%d%m%Y")
        filename = f"DonDatHang_{today}.xlsx"

        await query.message.reply_document(
            document=buf,
            filename=filename,
            caption=(
                f"✅ *File đặt hàng ngày {date.today().strftime('%d/%m/%Y')}*\n"
                f"📦 {len(items_list)} mặt hàng\n\n"
                f"_Gửi file này cho nhà cung cấp!_"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("Error building order file")
        await query.message.reply_text(f"❌ Lỗi tạo file: {e}")

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

# ─── SEARCH: /tim <keyword> ───────────────────────────────────────────
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
                CallbackQueryHandler(show_items, pattern="^cat:"),
                CallbackQueryHandler(done_order, pattern="^done$"),
            ],
            CHOOSING_ITEM: [
                CallbackQueryHandler(ask_qty, pattern="^item:"),
                CallbackQueryHandler(back_to_cat, pattern="^back_cat$"),
            ],
            ENTERING_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qty)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_yes, pattern="^confirm_yes$"),
                CallbackQueryHandler(confirm_no, pattern="^confirm_no$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("tim", cmd_search))
    app.add_handler(conv)

    logger.info("Bot đang chạy...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
