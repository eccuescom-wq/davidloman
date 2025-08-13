import logging, os
from dotenv import load_dotenv
from telegram.ext import Application
from bot_common_gsheets import register_handlers

load_dotenv()
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN")

PORT = int(os.environ.get("PORT", "10000"))
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("BASE_URL")
if not BASE_URL:
    raise RuntimeError("Missing BASE_URL (or RENDER_EXTERNAL_URL) for webhook URL")

SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "changeme")
WEBHOOK_PATH = f"webhook/{BOT_TOKEN}"

app = Application.builder().token(BOT_TOKEN).build()
register_handlers(app)

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=WEBHOOK_PATH,
    secret_token=SECRET,
    webhook_url=f"{BASE_URL}/{WEBHOOK_PATH}",
)
