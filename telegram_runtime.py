"""Shared Pyrogram client state for Telegram media retrieval."""

import asyncio
import logging
import os
import threading

from pyrogram import Client


logger = logging.getLogger("telegram.runtime")

Bot = Client(
    "vidstBot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    # Bot updates are received through Bot API long polling in bot.py.
    # Disable MTProto updates; this client is used for get_messages/stream_media.
    no_updates=True,
)

BOT_LOOP = None
BOT_READY = threading.Event()
BOT_ERROR = None


async def start_bot():
    """Start the Pyrogram client on the main asyncio loop."""
    global BOT_LOOP, BOT_ERROR
    try:
        BOT_LOOP = asyncio.get_running_loop()
        await Bot.start()
        logger.info("Pyrogram media client started (MTProto updates disabled).")
        BOT_READY.set()
    except Exception as exc:
        BOT_ERROR = exc
        BOT_READY.set()
        logger.exception("Pyrogram media client startup failed")
        raise


async def stop_bot():
    if Bot.is_connected:
        await Bot.stop()
