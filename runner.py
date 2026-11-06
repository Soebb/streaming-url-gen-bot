import os
import threading

from waitress import serve

from app import app
from telegram_runtime import run_bot, BOT_READY


bot_thread = threading.Thread(target=run_bot, name="telegram-bot", daemon=True)
bot_thread.start()

if not BOT_READY.wait(timeout=60):
    raise RuntimeError("Telegram bot did not start within 60 seconds")

serve(
    app,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
    threads=8,
)
