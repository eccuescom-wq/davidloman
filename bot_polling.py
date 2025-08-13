import logging, os
from dotenv import load_dotenv
from telegram.ext import Application
from bot_common_gsheets import register_handlers

load_dotenv()
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN")
app = Application.builder().token(BOT_TOKEN).build()
register_handlers(app)
app.run_polling()
