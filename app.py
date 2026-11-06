import asyncio
import inspect
import mimetypes
import os
import re
from math import ceil
from urllib.parse import unquote_plus

import requests
from flask import Flask, request, abort, Response, render_template
from werkzeug.utils import secure_filename
from yt_dlp import YoutubeDL

import telegram_runtime

Bot = telegram_runtime.Bot
from telegram_stream import decode_stream_token


app = Flask(__name__)


def b64_to_str(b64: str) -> str:
    import base64
    return base64.b64decode(b64.encode("ascii")).decode("utf-8")


def _submit(coro, timeout=60):
    if not telegram_runtime.BOT_READY.wait(timeout) or telegram_runtime.BOT_LOOP is None:
        raise RuntimeError("Telegram bot is not ready")
    return asyncio.run_coroutine_threadsafe(coro, telegram_runtime.BOT_LOOP).result(timeout=timeout)


def _raw_method(method):
    # Unwrap Pyrogram's synchronous wrapper. The raw function is unbound,
    # so callers must explicitly pass the Client instance as its first arg.
    return inspect.unwrap(method)


def _parse_range(range_header, file_size):
    if not range_header:
        return 0, file_size - 1, 200

    match = re.fullmatch(r"bytes=(\\d*)-(\\d*)", range_header.strip())
    if not match or (not match.group(1) and not match.group(2)):
        return None

    first, last = match.groups()
    if not first:
        suffix_length = int(last)
        if suffix_length <= 0:
            return None
        start = max(file_size - suffix_length, 0)
        end = file_size - 1
    else:
        start = int(first)
        end = int(last) if last else file_size - 1

    if start >= file_size or end < start:
        return None
    return start, min(end, file_size - 1), 206


async def _next_chunk(generator):
    return await generator.__anext__()


async def _close_generator(generator):
    await generator.aclose()


@app.route("/")
def homepage():
    return "Hello.."


@app.route("/tg/<token>", methods=["GET", "HEAD"])
def telegram_media(token):
    try:
        chat_id, message_id = decode_stream_token(token)
    except ValueError:
        abort(403)

    try:
        # inspect.unwrap() returns an unbound coroutine function.
        message = _submit(
            _raw_method(Bot.get_messages)(Bot, chat_id=chat_id, message_ids=message_id)
        )
        if isinstance(message, (list, tuple)):
            message = message[0] if message else None
    except Exception:
        app.logger.exception("Could not retrieve Telegram message")
        abort(502)

    if not message or getattr(message, "empty", False):
        abort(404)

    media = message.video or message.document or message.audio or message.animation
    if not media:
        abort(404)

    file_size = int(getattr(media, "file_size", 0) or 0)
    if file_size <= 0:
        abort(416)

    parsed_range = _parse_range(request.headers.get("Range"), file_size)
    if parsed_range is None:
        return Response(
            status=416,
            headers={"Content-Range": f"bytes */{file_size}", "Accept-Ranges": "bytes"},
        )

    start, end, status_code = parsed_range
    content_length = end - start + 1
    file_name = getattr(media, "file_name", "") or "video"
    mime_type = getattr(media, "mime_type", None) or ""
    if not mime_type.startswith(("video/", "audio/")):
        guessed_type = mimetypes.guess_type(file_name)[0]
        if guessed_type:
            mime_type = guessed_type
    mime_type = mime_type or "application/octet-stream"
    filename = secure_filename(getattr(media, "file_name", None) or "video")
    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(content_length),
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "private, no-store",
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    if request.method == "HEAD":
        return Response(status=status_code, headers=headers)

    chunk_size = 1024 * 1024
    chunk_offset = start // chunk_size
    first_chunk_skip = start % chunk_size
    chunk_limit = ceil((first_chunk_skip + content_length) / chunk_size)
    telegram_generator = _raw_method(Bot.stream_media)(
        Bot, message, offset=chunk_offset, limit=chunk_limit
    )

    def generate():
        skip = first_chunk_skip
        remaining = content_length
        try:
            while remaining > 0:
                try:
                    chunk = _submit(_next_chunk(telegram_generator), timeout=180)
                except StopAsyncIteration:
                    break
                piece = chunk[skip:]
                skip = 0
                if not piece:
                    continue
                piece = piece[:remaining]
                remaining -= len(piece)
                yield piece
        except GeneratorExit:
            raise
        except Exception:
            app.logger.exception("Telegram media streaming failed")
        finally:
            try:
                _submit(_close_generator(telegram_generator), timeout=10)
            except Exception:
                pass

    return Response(generate(), status=status_code, headers=headers, direct_passthrough=True)


@app.route("/yt")
def youtube():
    try:
        url = request.args["id"]
    except Exception:
        return "Please parse ?id= when calling the api", 400

    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
    video_name = info_dict["title"]
    videos = [
        {"format": fmt.get("height"), "url": fmt["url"]}
        for fmt in info_dict["formats"]
        if fmt.get("format_id") in ["18", "22"] and fmt.get("url")
    ]
    return render_template(
        "yt_template.html",
        video_name=video_name,
        videos=videos,
        video_captions=[],
    )


@app.route("/jw")
def jw_payer():
    try:
        video_id = request.args["id"]
    except Exception:
        return "Please parse ?id= when calling the api", 400
    encrypted = request.args.get("en", "1")
    if encrypted != "0":
        try:
            video_id = b64_to_str(video_id)
        except Exception:
            return "<font color=red size=15>Wrong Video ID</font> <br> ask at @JV_Community in Telegram"
    jw_url = "https://cdn.jwplayer.com/v2/media"
    video_response = requests.get(f"{jw_url}/{video_id}", timeout=20)
    if video_response.status_code != 200:
        return "<font color=red size=20>Wrong Video ID</font>"
    video = video_response.json()
    video_url = video["playlist"][0]["sources"][0]["file"]
    track_url = video["playlist"][0]["tracks"][0]["file"]
    return render_template("m3u8.html", video_url=video_url, track_url=track_url)


@app.route("/play")
def play():
    try:
        video_id = request.args["id"]
    except Exception:
        return "Please parse ?id= when calling the api", 400
    encrypted = request.args.get("en", "1")
    if encrypted != "0":
        try:
            video_id = b64_to_str(video_id)
        except Exception:
            return "<font color=red size=15>Wrong Video ID</font> <br> sorry"
    video_name = video_id.split("/")[-1]
    return render_template(
        "temp.html",
        type="jw",
        video_name=unquote_plus(video_name),
        video_url=video_id,
        track_url=video_id,
    )


@app.route("/m3u8")
def m3u8():
    try:
        video_url = request.args["id"]
    except Exception:
        return "Please parse ?id= when calling the api", 400
    encrypted = request.args.get("en", "1")
    if encrypted != "0":
        try:
            video_url = b64_to_str(video_url)
        except Exception:
            return "<font color=red size=15>Wrong Video ID</font> <br> sorry"
    return render_template("m3u8.html", video_url=video_url, track_url=video_url)
