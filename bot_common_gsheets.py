import os, re, logging
from typing import List, Optional
from datetime import datetime
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

import codes_gsheets as codesmod
import db as dbmod

logger = logging.getLogger("serial-bot-common")
TZ_NAME = os.environ.get("TZ", "Asia/Ho_Chi_Minh")

# prepare index
index = codesmod.CodesIndexGS()
count, _ = index.load()
logger.info("Loaded %s cells from Google Sheets; unique codes: %s", count, len(index.codes))

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo(TZ_NAME)
except Exception:
    _TZ = None

def fmt_dt(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str)
        if _TZ and dt.tzinfo is None:
            dt = dt.replace(tzinfo=_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str

def split_codes_from_text(text: str) -> List[str]:
    found = re.findall(r"[A-Za-z0-9][A-Za-z0-9._\-/]*", text or "")
    return found[:50]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin hãy nhập mã sản phẩm.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**Cách dùng**\n"
        "- Gửi mã trực tiếp (có thể nhiều mã, cách nhau bởi xuống dòng/khoảng trắng).\n"
        "- `/check <ma>` để kiểm tra 1 mã.\n"
        "- `/stats` xem số lượng mã đang index.\n"
        "- `/reload` tải lại dữ liệu từ Google Sheets (chỉ admin nếu cấu hình).",
        parse_mode="Markdown"
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 Số lượng mã đang index: {len(index.codes)}")

def is_admin(user_id: int) -> bool:
    ids = {int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x}
    return (user_id in ids) if ids else True  # nếu không set ADMIN_IDS, ai cũng /reload được

async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not is_admin(user.id):
        await update.message.reply_text("Bạn không có quyền /reload.")
        return
    count, _ = index.load()
    await update.message.reply_text(f"🔄 Đã tải lại. Số ô đọc được: {count} | Unique mã: {len(index.codes)}")

async def handle_codes(codes: List[str], update: Update):
    try:
        if index.maybe_reload():
            logger.info("Cache expired; reloaded. Unique codes: %s", len(index.codes))
    except Exception as e:
        logger.exception("maybe_reload failed", exc_info=e)
    lines = []
    for code in codes:
        is_known = index.contains(code)
        cnt, last = dbmod.bump(code, is_known=is_known)
        if is_known:
            msg = [f"✅ {code.upper()} — Sản phẩm chính hãng"]
        else:
            msg = [f"❌ {code.upper()} — Sản phẩm không chính hãng hoặc không phân phối tại đại lý Việt Nam"]
        msg.append(f"Ngày kiểm tra gần nhất: {fmt_dt(last)}")
        msg.append(f"Số lần kiểm tra: {cnt}")
        lines.append(" | ".join(msg))
    await update.message.reply_text("\n".join(lines))

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Vui lòng dùng: `/check <ma>`", parse_mode="Markdown")
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        await handle_codes([context.args[0]], update)
    except Exception as e:
        logger.exception("check_cmd failed", exc_info=e)
        await update.message.reply_text("⚠️ Lỗi khi kiểm tra mã. Vui lòng thử lại.")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    codes = split_codes_from_text(text)
    if not codes:
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        await handle_codes(codes, update)
    except Exception as e:
        logger.exception("on_text failed", exc_info=e)
        await update.message.reply_text("⚠️ Lỗi khi kiểm tra mã. Vui lòng thử lại.")

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Exception while handling an update:", exc_info=context.error)
    try:
        if isinstance(update, Update) and getattr(update, "effective_message", None):
            await update.effective_message.reply_text("⚠️ Đã xảy ra lỗi nội bộ. Vui lòng thử lại.")
    except Exception:
        pass

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("reload", reload_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_error_handler(on_error)
