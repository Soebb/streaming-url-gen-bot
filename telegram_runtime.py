"""Shared Pyrogram client and event loop for the bot and HTTP streamer."""

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


def run_bot():
    global BOT_LOOP, BOT_ERROR

    try:
        # Start Pyrogram on this thread so its synchronous wrapper creates
        # and owns the event loop that will also serve HTTP streaming calls.
        Bot.start()
        BOT_LOOP = asyncio.get_event_loop()
        BOT_READY.set()

        # idle() installs OS signal handlers and therefore cannot run in this
        # worker thread. Keep Pyrogram's loop alive without signal handling.
        BOT_LOOP.run_forever()
    except Exception as exc:
        BOT_ERROR = exc
        BOT_READY.set()
        raise
    finally:
        if Bot.is_connected:
            Bot.stop()
