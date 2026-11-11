from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping, Union

from .errors import ConfigurationError, SignatureError
from .messages import text
from .models import WebhookEvent

SIGNATURE_HEADER = "X-Webhook-Signature"
MAX_PAYLOAD = 256 * 1024
MAX_SIGNATURE = 200

Payload = Union[bytes, bytearray, str]


def _bytes(payload: Payload) -> bytes:
    return payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)


def sign(secret: str, payload: Payload) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), _bytes(payload), hashlib.sha256).hexdigest()


def matches(secret: str, payload: Payload, signature: str) -> bool:
    if not secret or not signature or len(signature) > MAX_SIGNATURE:
        return False
    body = _bytes(payload)
    if len(body) > MAX_PAYLOAD:
        return False
    expected = sign(secret, body).removeprefix("sha256=")
    received = signature.strip().removeprefix("sha256=").lower()
    return hmac.compare_digest(expected, received)


def header(headers: Mapping[str, Any]) -> str:
    for name, value in headers.items():
        if str(name).lower() == SIGNATURE_HEADER.lower():
            return str(value)
    return ""


def verify_webhook(secret: str, payload: Payload, signature: str) -> WebhookEvent:
    if not secret:
        raise ConfigurationError(text("error.missing_secret"))
    body = _bytes(payload)
    if len(body) > MAX_PAYLOAD:
        raise SignatureError(text("error.payload_size", limit=MAX_PAYLOAD))
    if not matches(secret, body, signature):
        raise SignatureError(text("error.signature"))
    return parse_webhook(body)


def parse_webhook(payload: Payload) -> WebhookEvent:
    try:
        data = json.loads(_bytes(payload))
    except ValueError:
        raise SignatureError(text("error.payload")) from None
    if not isinstance(data, Mapping) or not data:
        raise SignatureError(text("error.payload"))
    return WebhookEvent.from_api(data)
