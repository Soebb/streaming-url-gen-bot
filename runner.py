"""Application entry point: Pyrogram media client + Telegram webhook + HTTP server."""

import asyncio
import logging
import os
import threading

import bot
from app import app
from telegram_runtime import start_bot, stop_bot
from waitress import create_server


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("runner")
HTTP_READY = threading.Event()


def run_http_server():
    port = int(os.environ.get("PORT", "10000"))
    logger.info("Starting HTTP server on 0.0.0.0:%s", port)
    server = create_server(app, host="0.0.0.0", port=port, threads=8)
    HTTP_READY.set()
    server.run()


async def main():
    logger.info("Starting Pyrogram media client...")
    await start_bot()

    http_thread = threading.Thread(
        target=run_http_server,
        name="http-server",
        daemon=True,
    )
    http_thread.start()

    if not HTTP_READY.wait(timeout=20):
        raise RuntimeError("HTTP server did not become ready in time.")

    bot.configure_webhook()
    logger.info("HTTP server and Telegram webhook are ready.")

    try:
        await asyncio.Event().wait()
    finally:
        logger.info("Stopping Pyrogram media client...")
        await stop_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception:
        logger.exception("Application startup/runtime failed")
        raise
