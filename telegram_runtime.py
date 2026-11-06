"""Shared Pyrogram client state for HTTP handlers."""

import asyncio
import os
import threading

from pyrogram import Client


Bot = Client(
    "vidstBot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
)

BOT_LOOP = None
BOT_READY = threading.Event()
BOT_ERROR = None


async def start_bot():
    """Start Pyrogram on the main asyncio loop and keep that loop alive."""
    global BOT_LOOP, BOT_ERROR

    try:
        BOT_LOOP = asyncio.get_running_loop()
        await Bot.start()
        BOT_READY.set()
    except Exception as exc:
        BOT_ERROR = exc
        BOT_READY.set()
        raise


async def stop_bot():
    if Bot.is_connected:
        await Bot.stop()
