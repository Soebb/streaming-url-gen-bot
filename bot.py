"""Telegram Bot API long-polling handlers.

Pyrogram is retained only for MTProto media retrieval/streaming. Updates are
received through the official HTTPS Bot API to avoid the stalled MTProto
updates stream observed on the deployment.
"""

import base64
import logging
import os
import re
import threading
import time
from urllib.parse import quote_plus, urlparse

import requests

from telegram_stream import create_stream_token


logger = logging.getLogger("telegram.handlers")
BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
APP_URL = (os.environ.get("DOPRAX_APP_URL") or os.environ.get("RENDER_EXTERNAL_URL") or "").strip()
MAX_VIDEO_SIZE = int(os.environ.get("MAX_VIDEO_SIZE", str(2 * 1024 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v",
    ".mpeg", ".mpg", ".3gp", ".ts", ".wmv", ".flv",
}
POLLING_STOP = threading.Event()


def get_app_base_url():
    if not APP_URL:
        return None
    if not re.match(r"^https?://", APP_URL, re.IGNORECASE):
        return "https://" + APP_URL.rstrip("/")
    return APP_URL.rstrip("/")


def api_call(method, payload=None, timeout=20):
    response = requests.post(
        f"{BOT_API}/{method}",
        json=payload or {},
        timeout=timeout,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram Bot API {method} failed: {result}")
    return result["result"]


def reply(chat_id, text, reply_to=None, disable_preview=True):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_preview,
    }
    if reply_to is not None:
        payload["reply_to_message_id"] = reply_to
        payload["allow_sending_without_reply"] = True
    api_call("sendMessage", payload)


def handle_message(message):
    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        return

    chat_id = chat.get("id")
    message_id = message.get("message_id")
    text = (message.get("text") or "").strip()
    logger.info(
        "Incoming private message received: chat_id=%s message_id=%s type=%s",
        chat_id,
        message_id,
        "video" if message.get("video") else "document" if message.get("document") else "text" if text else "other",
    )

    if text.split(maxsplit=1)[0].split("@")[0] == "/start" if text else False:
        first_name = (message.get("from") or {}).get("first_name") or "there"
        reply(
            chat_id,
            f"Hi {first_name}, I'm streaming link gen bot.\\n\\n"
            "Send a YouTube video URL, a direct video download URL, or upload a video here.",
            message_id,
        )
        return

    media = message.get("video") or message.get("document")
    if media:
        original_name = media.get("file_name") or "video.mp4"
        extension = os.path.splitext(os.path.basename(original_name))[1].lower()
        mime_type = (media.get("mime_type") or "").lower()
        if not (mime_type.startswith("video/") or extension in ALLOWED_EXTENSIONS):
            reply(chat_id, "Please send a video file (as a video or document).", message_id)
            return

        file_size = int(media.get("file_size") or 0)
        if file_size and file_size > MAX_VIDEO_SIZE:
            max_mb = MAX_VIDEO_SIZE // (1024 * 1024)
            reply(chat_id, f"Video is too large. Maximum allowed size is {max_mb} MB.", message_id)
            return

        base_url = get_app_base_url()
        if not base_url:
            reply(chat_id, "The bot administrator has not configured the public app URL.", message_id)
            return

        token = create_stream_token(chat_id, message_id)
        media_url = f"{base_url}/tg/{token}"
        encoded_url = base64.b64encode(media_url.encode("utf-8")).decode("ascii")
        stream_url = f"{base_url}/play?id={quote_plus(encoded_url)}"
        reply(
            chat_id,
            "Your video is ready to stream directly from Telegram:\\n" + stream_url,
            message_id,
            disable_preview=False,
        )
        return

    if text:
        base_url = get_app_base_url()
        if not base_url:
            reply(chat_id, "The bot administrator has not configured the public app URL.", message_id)
            return
        if os.path.splitext(urlparse(text).path)[1].lower() in ALLOWED_EXTENSIONS:
            url = f"{base_url}/play?id=" + quote_plus(text) + "&en=0"
        else:
            url = f"{base_url}/yt?id=" + quote_plus(text)
        reply(chat_id, url, message_id)


def polling_loop():
    logger.info("Starting Telegram Bot API long polling.")
    try:
        webhook = api_call("getWebhookInfo")
        logger.info(
            "Telegram webhook status before polling: configured=%s pending_updates=%s",
            bool(webhook.get("url")),
            webhook.get("pending_update_count", 0),
        )
        if webhook.get("url"):
            api_call("deleteWebhook", {"drop_pending_updates": False})
            logger.warning("Removed existing Telegram webhook to enable long polling.")

        me = api_call("getMe")
        logger.info("Telegram Bot API authenticated as @%s (id=%s).", me.get("username"), me.get("id"))
    except Exception:
        logger.exception("Telegram Bot API initialization failed.")
        return

    offset = None
    while not POLLING_STOP.is_set():
        try:
            payload = {"timeout": 50, "allowed_updates": ["message"]}
            if offset is not None:
                payload["offset"] = offset
            updates = api_call("getUpdates", payload, timeout=65)
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message:
                    continue
                try:
                    handle_message(message)
                except Exception:
                    logger.exception(
                        "Failed to process Telegram update_id=%s",
                        update.get("update_id"),
                    )
        except requests.RequestException:
            logger.exception("Telegram long-poll request failed; retrying in 5 seconds.")
            POLLING_STOP.wait(5)
        except Exception:
            logger.exception("Telegram polling failed; retrying in 5 seconds.")
            POLLING_STOP.wait(5)

    logger.info("Telegram Bot API polling stopped.")
