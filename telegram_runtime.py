"""Shared Telegram client state for HTTP handlers."""

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
    # Process pending updates rather than silently discarding them at startup.
    skip_updates=False,
)

BOT_LOOP = None
BOT_READY = threading.Event()
BOT_ERROR = None


async def start_bot():
    """Start the Telegram client on the main asyncio loop."""
    global BOT_LOOP, BOT_ERROR

    try:
        BOT_LOOP = asyncio.get_running_loop()
        await Bot.start()
        logger.info("Telegram client started; attempting update-gap recovery.")

        # The original Pyrogram 2.0.106 only logged UpdatesTooLong and did
        # not recover the missing update state. Pyrofork exposes recover_gaps().
        recovered = await Bot.recover_gaps()
        logger.info(
            "Telegram update recovery finished: %s messages, %s other updates.",
            recovered[0],
            recovered[1],
        )
        BOT_READY.set()
    except Exception as exc:
        BOT_ERROR = exc
        BOT_READY.set()
        logger.exception("Telegram client startup/update recovery failed")
        raise


async def stop_bot():
    if Bot.is_connected:
        await Bot.stop()
