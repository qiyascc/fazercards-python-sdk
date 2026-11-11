from __future__ import annotations

import json

import pytest

from fazercards_sdk import ConfigurationError, FazerCards, OrderStatus, SignatureError, webhooks

from .conftest import KEY, SECRET, gift_order


def _signed(body):
    raw = json.dumps(body).encode()
    return raw, webhooks.sign(SECRET, raw)


def test_a_signed_order_event_is_read(fc):
    raw, signature = _signed(gift_order())
    event = fc.verify_webhook(raw, signature)
    assert event.order_id == "ord-1001" and event.status is OrderStatus.COMPLETED
    assert event.order is not None and event.order.codes == ("ABCD-1234-EFGH",) and not event.needs_lookup


def test_the_signature_can_come_from_the_headers(fc):
    raw, signature = _signed(gift_order())
    assert fc.verify_webhook(raw, headers={"X-Webhook-Signature": signature}).order_id == "ord-1001"


def test_a_bare_hex_signature_is_accepted(fc):
    raw, signature = _signed(gift_order())
    assert fc.verify_webhook(raw, signature.removeprefix("sha256=")).order_id == "ord-1001"


@pytest.mark.parametrize("body", [
    {"data": {"id": "ord-5", "status": "failed"}},
    {"order_id": "ord-5", "status": "failed"},
    {"order": {"order": {"id": "ord-5", "status": "failed"}}},
])
def test_every_payload_shape(fc, body):
    raw, signature = _signed(body)
    event = fc.verify_webhook(raw, signature)
    assert event.order_id == "ord-5" and event.status.failed


def test_an_event_without_a_status_asks_for_a_lookup(fc):
    raw, signature = _signed({"order_id": "ord-5", "merchant_txn_id": "GNET-1-2"})
    event = fc.verify_webhook(raw, signature)
    assert event.needs_lookup and event.merchant_txn_id == "GNET-1-2"


def test_a_changed_body_is_refused(fc):
    raw, signature = _signed(gift_order())
    with pytest.raises(SignatureError):
        fc.verify_webhook(raw.replace(b"completed", b"failed"), signature)


def test_a_huge_body_is_refused_before_hashing(fc):
    raw = b"{" + b" " * (webhooks.MAX_PAYLOAD + 1) + b"}"
    with pytest.raises(SignatureError):
        fc.verify_webhook(raw, webhooks.sign(SECRET, raw))


def test_a_body_that_is_not_an_object_is_refused(fc):
    raw = b"[1, 2]"
    with pytest.raises(SignatureError):
        fc.verify_webhook(raw, webhooks.sign(SECRET, raw))


def test_no_secret_means_no_check():
    client = FazerCards(KEY)
    with pytest.raises(ConfigurationError):
        client.verify_webhook(b"{}", "sha256=00")
    assert not webhooks.matches("", b"{}", "sha256=00")
