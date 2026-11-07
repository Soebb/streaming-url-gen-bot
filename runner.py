"""Application entry point: Pyrogram media client + Bot API polling."""

import asyncio
import logging
import os
import threading

import bot
from app import app
from telegram_runtime import start_bot, stop_bot
from waitress import serve


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("runner")


def run_http_server():
    port = int(os.environ.get("PORT", "10000"))
    logger.info("Starting HTTP server on 0.0.0.0:%s", port)
    serve(app, host="0.0.0.0", port=port, threads=8)


async def main():
    logger.info("Starting Pyrogram media client...")
    await start_bot()

    polling_thread = threading.Thread(
        target=bot.polling_loop,
        name="telegram-bot-api-polling",
        daemon=True,
    )
    polling_thread.start()

    http_thread = threading.Thread(
        target=run_http_server,
        name="http-server",
        daemon=True,
    )
    http_thread.start()
    logger.info("HTTP server and Telegram Bot API polling threads started.")

    try:
        await asyncio.Event().wait()
    finally:
        logger.info("Stopping Telegram services...")
        bot.POLLING_STOP.set()
        await stop_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception:
        logger.exception("Application startup/runtime failed")
        raise
