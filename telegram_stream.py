"""Signed, stateless references to Telegram messages containing media."""

import base64
import hashlib
import hmac
import json
import os


def _secret() -> bytes:
    secret = os.environ.get("STREAM_SECRET") or os.environ.get("BOT_TOKEN")
    if not secret:
        raise RuntimeError("BOT_TOKEN or STREAM_SECRET must be configured")
    return secret.encode("utf-8")


def create_stream_token(chat_id: int, message_id: int) -> str:
    payload = json.dumps({"c": int(chat_id), "m": int(message_id)}, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_stream_token(token: str) -> tuple[int, int]:
    try:
        encoded, supplied_signature = token.rsplit(".", 1)
        expected_signature = hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid stream link signature")
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        chat_id, message_id = int(payload["c"]), int(payload["m"])
        if message_id <= 0:
            raise ValueError("Invalid message ID")
        return chat_id, message_id
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid stream link") from exc
