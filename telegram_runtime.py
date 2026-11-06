"""Shared Pyrogram client and event loop for the bot and HTTP streamer."""

import asyncio
import threading

from pyrogram import Client, idle


Bot = Client(
    "vidstBot",
    bot_token=__import__("os").environ["BOT_TOKEN"],
    api_id=int(__import__("os").environ["API_ID"]),
    api_hash=__import__("os").environ["API_HASH"],
)

BOT_LOOP = None
BOT_READY = threading.Event()


def run_bot():
    global BOT_LOOP
    Bot.start()
    BOT_LOOP = asyncio.get_event_loop()
    BOT_READY.set()
    idle()
    Bot.stop()
