"""Inline keyboard builders for Order Bot."""
from datetime import date, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def fmt_qty(q: float) -> str:
    """Format quantity for display."""
    return str(int(q)) if q == int(q) else str(q)


def edit_screen_kbd(order: dict) -> InlineKeyboardMarkup:
    """Keyboard for edit order screen."""
    btns = []
    for code, item in order.items():
        lbl = f"{item['name']}: {fmt_qty(item['qty'])} {item['unit']}"
        if len(lbl) > 38:
            lbl = lbl[:35] + "..."
        btns.append([InlineKeyboardButton(f"✏️ {lbl}", callback_data=f"ei:{code}")])
    btns.append([InlineKeyboardButton("➕ Thêm mặt hàng", callback_data="add_item")])
    btns.append([
        InlineKeyboardButton("✅ Xong – Xác nhận", callback_data="done_editing"),
        InlineKeyboardButton("💾 Lưu mẫu", callback_data="save_tpl_btn"),
    ])
    return InlineKeyboardMarkup(btns)


def category_kbd(cats: dict) -> InlineKeyboardMarkup:
    """Keyboard for category selection."""
    btns = [[InlineKeyboardButton(f"📁 {cat} ({len(items)})", callback_data=f"cat:{cat}")]
            for cat, items in cats.items()]
    btns.append([InlineKeyboardButton("↩️ Quay lại đơn", callback_data="cat:back")])
    return InlineKeyboardMarkup(btns)


def item_kbd(items: list, cat: str) -> InlineKeyboardMarkup:
    """Keyboard for item selection within a category."""
    btns = []
    for it in items:
        lbl = f"{it['name']} ({it['unit']})"
        if len(lbl) > 40:
            lbl = lbl[:37] + "..."
        btns.append([InlineKeyboardButton(lbl, callback_data=f"item:{it['code']}")])
    btns.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="cat:back")])
    return InlineKeyboardMarkup(btns)


def edit_item_kbd() -> InlineKeyboardMarkup:
    """Keyboard for editing item quantity."""
    btns = [
        [InlineKeyboardButton(str(i), callback_data=f"eq:{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"eq:{i}") for i in range(6, 11)],
        [
            InlineKeyboardButton("✏️ Nhập số khác", callback_data="eq:custom"),
            InlineKeyboardButton("🗑️ Xoá món này", callback_data="eq:remove"),
        ],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="eq:back")],
    ]
    return InlineKeyboardMarkup(btns)


def confirm_kbd(order_date: date) -> tuple[str, InlineKeyboardMarkup]:
    """Keyboard for order confirmation."""
    lines = ["📋 *Xác nhận đơn đặt hàng:*\n"]
    # This is called with order items context, return markup only
    btns = [
        [
            InlineKeyboardButton("✅ Tạo file Excel", callback_data="confirm_yes"),
            InlineKeyboardButton("📅 Đổi ngày", callback_data="change_date"),
        ],
        [
            InlineKeyboardButton("✏️ Sửa tiếp", callback_data="back_to_edit"),
            InlineKeyboardButton("❌ Huỷ", callback_data="confirm_no"),
        ],
    ]
    return "\n", InlineKeyboardMarkup(btns)


def history_kbd(dates: list, get_order_fn) -> InlineKeyboardMarkup:
    """Keyboard for history date selection."""
    btns = []
    for ds in dates:
        d = date.fromisoformat(ds)
        n = len(get_order_fn(d) or [])
        btns.append([InlineKeyboardButton(
            f"📅 {d.strftime('%d/%m/%Y')} — {n} món",
            callback_data=f"hi:{ds}"
        )])
    btns.append([InlineKeyboardButton("🔍 Nhập ngày cụ thể", callback_data="hi:custom")])
    btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="hi:back")])
    return InlineKeyboardMarkup(btns)


def date_kbd() -> InlineKeyboardMarkup:
    """Keyboard for date selection."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    btns = [
        [InlineKeyboardButton(f"⬅️ {yesterday.strftime('%d/%m/%Y')} (hôm qua)",
                             callback_data=f"qdate:{yesterday.isoformat()}")],
        [InlineKeyboardButton(f"📅 {today.strftime('%d/%m/%Y')} (hôm nay)",
                             callback_data=f"qdate:{today.isoformat()}")],
        [InlineKeyboardButton(f"➡️ {tomorrow.strftime('%d/%m/%Y')} (ngày mai)",
                             callback_data=f"qdate:{tomorrow.isoformat()}")],
        [InlineKeyboardButton("✏️ Nhập ngày khác (DD/MM/YYYY)", callback_data="qdate:custom")],
        [InlineKeyboardButton("↩️ Quay lại", callback_data="qdate:back")],
    ]
    return InlineKeyboardMarkup(btns)


def entry_point_kbd(recent: list, tmpls: list) -> InlineKeyboardMarkup:
    """Keyboard for order entry point."""
    btns = []
    if recent:
        d = date.fromisoformat(recent[0])
        from data import get_order
        n = len(get_order(d) or [])
        btns.append([InlineKeyboardButton(
            f"🔄 Đơn gần nhất ({d.strftime('%d/%m/%Y')} — {n} món)",
            callback_data="en:recent"
        )])
    if len(tmpls) == 1:
        btns.append([InlineKeyboardButton(
            f"📋 Từ mẫu: {tmpls[0]['name']}",
            callback_data=f"en:tpl:{tmpls[0]['_id']}"
        )])
    elif len(tmpls) > 1:
        btns.append([InlineKeyboardButton("📋 Từ mẫu đã lưu", callback_data="en:tmpls")])
    btns.append([InlineKeyboardButton("📅 Từ đơn ngày khác", callback_data="en:hist")])
    btns.append([InlineKeyboardButton("✏️ Tạo mới hoàn toàn", callback_data="en:new")])
    return InlineKeyboardMarkup(btns)


def template_menu_kbd(tmpls: list) -> InlineKeyboardMarkup:
    """Keyboard for template selection."""
    btns = [[InlineKeyboardButton(f"📋 {t['name']}", callback_data=f"en:tpl:{t['_id']}")]
            for t in tmpls]
    btns.append([InlineKeyboardButton("↩️ Quay lại", callback_data="en:back_main")])
    return InlineKeyboardMarkup(btns)


def template_save_kbd() -> InlineKeyboardMarkup:
    """Keyboard for template save options."""
    from data import list_templates
    tmpls = list_templates()
    btns = [[InlineKeyboardButton(f"📋 Ghi đè: {t['name']}", callback_data=f"tpl_ow:{t['_id']}")]
            for t in tmpls]
    btns.append([InlineKeyboardButton("✨ Tạo mẫu mới", callback_data="tpl_new")])
    btns.append([InlineKeyboardButton("↩️ Huỷ", callback_data="tpl_cancel")])
    return InlineKeyboardMarkup(btns)
