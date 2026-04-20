"""Search command handler."""
from telegram import Update
from telegram.ext import ContextTypes


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tim command - search for items."""
    if not ctx.args:
        await update.message.reply_text("Cú pháp: /tim <từ khoá>\nVD: /tim thịt bò")
        return

    kw = " ".join(ctx.args).lower()
    items = ctx.bot_data.get("items", {})
    found = [v for v in items.values() if kw in v["name"].lower()]

    if not found:
        await update.message.reply_text(f"❌ Không tìm thấy '{kw}'")
        return

    lines = [f"🔍 *Kết quả '{kw}':*\n"]
    for it in found[:20]:
        lines.append(f"  `{it['code']}` {it['name']} ({it['unit']}) — {it['ncc']}")
    if len(found) > 20:
        lines.append(f"\n_...và {len(found) - 20} kết quả khác_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
