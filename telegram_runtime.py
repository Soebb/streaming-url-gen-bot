"""Shared Pyrogram client and event loop for the bot and HTTP streamer."""

import asyncio
import os
import threading

from pyrogram import Client, idle


Bot = Client(
    "vidstBot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
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
