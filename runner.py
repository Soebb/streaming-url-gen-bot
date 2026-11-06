"""Application entry point: Pyrogram owns the main asyncio loop."""

import asyncio
import logging
import os
import threading

import bot  # Register message handlers before starting Pyrogram.
from app import app
from telegram_runtime import start_bot, stop_bot, BOT_READY, BOT_ERROR

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
    logger.info("Starting Telegram bot...")
    await start_bot()
    logger.info("Telegram bot connected and polling for updates.")

    http_thread = threading.Thread(
        target=run_http_server,
        name="http-server",
        daemon=True,
    )
    http_thread.start()
    logger.info("HTTP server thread started.")

    try:
        # Keep the main asyncio loop alive; Pyrogram receives updates here.
        await asyncio.Event().wait()
    finally:
        logger.info("Stopping Telegram bot...")
        await stop_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception:
        logger.exception("Application startup/runtime failed")
        raise
