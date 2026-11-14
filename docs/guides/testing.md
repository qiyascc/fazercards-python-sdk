# Testing your code

Never test a shop against the real FazerCards API: every test order would spend money. Give the client an `httpx.Client` with an `httpx.MockTransport`, and every request goes to a function of yours.

## A complete test

Your code:

```python
from fazercards_sdk import FazerCards


def sell_card(fc: FazerCards, shop_order: str) -> tuple[str, ...]:
    order = fc.giftcards.order("playstation_tr", "250_try", idempotency_key=shop_order)
    if order.awaiting_codes:
        return ()
    return order.codes
```

The test:

```python
import json

import httpx
import pytest

from fazercards_sdk import FazerCards, KeyCollisionError


def order(status="completed", cards=("ABCD-1234-EFGH",), card_id="250_try"):
    return {"ok": True, "order": {"id": "ord-1", "kind": "gift_card", "status": status,
                                  "category_id": "playstation_tr", "card_id": card_id, "cards": list(cards)}}


def client(handler) -> FazerCards:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return FazerCards("test-key", max_retries=0, code_check_wait=0, http_client=http)


def test_codes_are_returned():
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(200, json=order())

    assert sell_card(client(handler), "ORDER-1") == ("ABCD-1234-EFGH",)
    assert sent[0].headers["Idempotency-Key"] == "ORDER-1"
    assert json.loads(sent[0].content) == {"category_id": "playstation_tr", "card_id": "250_try", "quantity": 1}


def test_late_codes_are_read_again():
    replies = [order(cards=()), order()]

    def handler(request):
        return httpx.Response(200, json=replies.pop(0))

    assert sell_card(client(handler), "ORDER-2") == ("ABCD-1234-EFGH",)


def test_a_reused_key_for_another_card_is_refused():
    def handler(request):
        return httpx.Response(200, json=order(card_id="500_try"))

    with pytest.raises(KeyCollisionError):
        sell_card(client(handler), "ORDER-3")
```

- `max_retries=0` keeps failing tests fast.
- `code_check_wait=0` removes the pause between gift card code reads.
- The test checks the `Idempotency-Key` header, which is the most important thing a shop sends.

## Webhooks

Sign a body with the same function the SDK checks with:

```python
import json

from fazercards_sdk import FazerCards, webhooks

SECRET = "test-secret"


def test_webhook():
    fc = FazerCards("test-key", webhook_secret=SECRET)
    body = json.dumps({"order": {"id": "ord-1", "kind": "gift_card", "status": "completed", "cards": ["X"]}}).encode()
    event = fc.verify_webhook(body, headers={"X-Webhook-Signature": webhooks.sign(SECRET, body)})
    assert event.order.codes == ("X",)
```

## Failures

```python
from fazercards_sdk import OutcomeUnknownError


def test_order_times_out():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(OutcomeUnknownError) as info:
        sell_card(client(handler), "ORDER-4")
    assert info.value.idempotency_key == "ORDER-4"
```

The SDK's own [tests/conftest.py](https://github.com/qiyascc/fazercards-python-sdk/blob/main/tests/conftest.py) has realistic order bodies for every kind of order.
