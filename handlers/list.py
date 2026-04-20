"""List command handler."""
from telegram import Update
from telegram.ext import ContextTypes


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command - show all food items."""
    items = ctx.bot_data.get("items", {})
    categories = ctx.bot_data.get("categories", {})

    MAX_LEN = 3800
    lines = [f"📦 *Danh sách ({len(items)} sản phẩm):*"]
    buf = []

    for cat, cat_items in categories.items():
        block = [f"\n*{cat}* ({len(cat_items)} món):"]
        for it in cat_items[:5]:
            block.append(f"  • `{it['code']}` {it['name']} ({it['unit']})")
        if len(cat_items) > 5:
            block.append(f"  _...và {len(cat_items) - 5} món khác_")

        if len("\n".join(lines + buf + block)) > MAX_LEN:
            await update.message.reply_text("\n".join(lines + buf), parse_mode="Markdown")
            lines = []
            buf = block
        else:
            buf.extend(block)

    if lines or buf:
        await update.message.reply_text("\n".join(lines + buf), parse_mode="Markdown")
