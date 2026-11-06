import base64
import logging
import os
import re
from urllib.parse import quote_plus, urlparse

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_runtime import Bot
from telegram_stream import create_stream_token


logger = logging.getLogger("telegram.handlers")

APP_URL = (os.environ.get("DOPRAX_APP_URL") or os.environ.get("RENDER_EXTERNAL_URL") or "").strip()
MAX_VIDEO_SIZE = int(os.environ.get("MAX_VIDEO_SIZE", str(2 * 1024 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v",
    ".mpeg", ".mpg", ".3gp", ".ts", ".wmv", ".flv",
}

START_TXT = """
Hi {}, I'm streaming link gen bot.

Send a YouTube video URL, a direct video download URL, or upload a video here.
"""

START_BTN = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Source Code", url="https://github.com/soebb")]]
)


def get_app_base_url():
    if not APP_URL:
        return None
    if not re.match(r"^https?://", APP_URL, re.IGNORECASE):
        return "https://" + APP_URL.rstrip("/")
    return APP_URL.rstrip("/")


# Diagnostic handler: confirms whether Telegram updates reach Pyrogram at all.
# Group -1 lets the normal command/media handlers in group 0 run afterward.
@Bot.on_message(filters.private & filters.incoming, group=-1)
async def log_incoming_message(_, message):
    logger.info(
        "Incoming private message received: chat_id=%s message_id=%s type=%s",
        message.chat.id if message.chat else None,
        message.id,
        message.media.value if message.media else ("text" if message.text else "other"),
    )


@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    logger.info("Handling /start from chat_id=%s", update.chat.id)
    await update.reply_text(
        text=START_TXT.format(update.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=START_BTN,
    )


@Bot.on_message(filters.private & (filters.video | filters.document))
async def receive_video(client, message):
    logger.info("Handling video/document from chat_id=%s", message.chat.id)
    media = message.video or message.document
    if not media:
        return

    original_name = getattr(media, "file_name", None) or "video.mp4"
    extension = os.path.splitext(os.path.basename(original_name))[1].lower()
    mime_type = (getattr(media, "mime_type", None) or "").lower()

    if not (mime_type.startswith("video/") or extension in ALLOWED_EXTENSIONS):
        await message.reply_text("Please send a video file (as a video or document).")
        return

    file_size = getattr(media, "file_size", 0) or 0
    if file_size and file_size > MAX_VIDEO_SIZE:
        max_mb = MAX_VIDEO_SIZE // (1024 * 1024)
        await message.reply_text(f"Video is too large. Maximum allowed size is {max_mb} MB.")
        return

    base_url = get_app_base_url()
    if not base_url:
        await message.reply_text("The bot administrator has not configured the public app URL.")
        return

    try:
        token = create_stream_token(message.chat.id, message.id)
        media_url = f"{base_url}/tg/{token}"
        encoded_url = base64.b64encode(media_url.encode("utf-8")).decode("ascii")
        stream_url = f"{base_url}/play?id={quote_plus(encoded_url)}"
        await message.reply_text(
            "Your video is ready to stream directly from Telegram:\\n" + stream_url,
            disable_web_page_preview=False,
        )
    except Exception:
        logger.exception("Failed to create stream link for chat_id=%s", message.chat.id)
        await message.reply_text("Could not create the stream link. Please try again.")


@Bot.on_message(filters.private & filters.text)
async def st(_, m):
    logger.info("Handling text message from chat_id=%s", m.chat.id)
    vid_url = m.text.strip()
    base_url = get_app_base_url()
    if not base_url:
        await m.reply_text("The bot administrator has not configured the public app URL.")
        return

    if os.path.splitext(urlparse(vid_url).path)[1].lower() in ALLOWED_EXTENSIONS:
        url = f"{base_url}/play?id=" + quote_plus(vid_url) + "&en=0"
    else:
        url = f"{base_url}/yt?id=" + quote_plus(vid_url)

    await m.reply(url)
