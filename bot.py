import base64
import mimetypes
import os
import re
import uuid
from urllib.parse import quote_plus, urlparse

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


APP_URL = os.environ.get("DOPRAX_APP_URL", "").strip()
MEDIA_DIR = os.environ.get(
    "MEDIA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
)
MAX_VIDEO_SIZE = int(os.environ.get("MAX_VIDEO_SIZE", str(2 * 1024 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v",
    ".mpeg", ".mpg", ".3gp", ".ts", ".wmv", ".flv",
}

os.makedirs(MEDIA_DIR, exist_ok=True)

Bot = Client(
    "vidstBot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
)


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


@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    await update.reply_text(
        text=START_TXT.format(update.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=START_BTN,
    )


@Bot.on_message(filters.private & (filters.video | filters.document))
async def receive_video(client, message):
    media = message.video or message.document
    if not media:
        return

    original_name = getattr(media, "file_name", None) or "video.mp4"
    extension = os.path.splitext(os.path.basename(original_name))[1].lower()
    mime_type = (getattr(media, "mime_type", None) or "").lower()

    # Documents are accepted only when their MIME type or extension indicates video.
    if not (mime_type.startswith("video/") or extension in ALLOWED_EXTENSIONS):
        await message.reply_text("Please send a video file (as a video or document).")
        return

    if extension not in ALLOWED_EXTENSIONS:
        guessed_extension = mimetypes.guess_extension(mime_type) if mime_type else None
        extension = guessed_extension if guessed_extension in ALLOWED_EXTENSIONS else ".mp4"

    file_size = getattr(media, "file_size", 0) or 0
    if file_size and file_size > MAX_VIDEO_SIZE:
        max_mb = MAX_VIDEO_SIZE // (1024 * 1024)
        await message.reply_text(f"Video is too large. Maximum allowed size is {max_mb} MB.")
        return

    base_url = get_app_base_url()
    if not base_url:
        await message.reply_text("The bot administrator has not configured DOPRAX_APP_URL.")
        return

    stored_name = f"{uuid.uuid4().hex}{extension}"
    target_path = os.path.join(MEDIA_DIR, stored_name)
    status = await message.reply_text("Downloading your video from Telegram...")

    try:
        downloaded_path = await client.download_media(message, file_name=target_path)
        if not downloaded_path or not os.path.isfile(downloaded_path):
            await status.edit_text("Download failed. Please try sending the video again.")
            return

        media_url = f"{base_url}/media/{stored_name}"
        encoded_url = base64.b64encode(media_url.encode("utf-8")).decode("ascii")
        stream_url = f"{base_url}/play?id={quote_plus(encoded_url)}"

        await status.edit_text(
            "Your video is ready to stream:\n" + stream_url,
            disable_web_page_preview=False,
        )
    except Exception as exc:
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass
        await status.edit_text(f"Could not download the video: {exc}")


@Bot.on_message(filters.private & filters.text)
async def st(_, m):
    vid_url = m.text.strip()
    base_url = get_app_base_url()
    if not base_url:
        await m.reply_text("The bot administrator has not configured DOPRAX_APP_URL.")
        return

    if os.path.splitext(urlparse(vid_url).path)[1].lower() in ALLOWED_EXTENSIONS:
        url = f"{base_url}/play?id=" + quote_plus(vid_url) + "&en=0"
    else:
        url = f"{base_url}/yt?id=" + quote_plus(vid_url)

    await m.reply(url)


Bot.run()
