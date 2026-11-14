# Webhooks

FazerCards can call your server when an order changes, so you do not have to poll. Each call is a POST with a JSON body, signed with your webhook secret in the `X-Webhook-Signature` header.

## Set the address

```python
hook = fc.account.set_webhook("https://shop.example/webhook/fazercards")
print(hook.url, hook.enabled)
```

The address must be https. `fc.account.webhook()` reads the current setting:

| `Webhook` field | Meaning |
| --- | --- |
| `url` | The address FazerCards calls |
| `enabled` | Whether calls are being made |
| `consecutive_failures` | Failed deliveries in a row |
| `last_success_at`, `last_failure_at` | Timestamps of the last delivery attempts |
| `last_failure_reason` | Why the last delivery failed |
| `created_at`, `updated_at` | When the setting was made and changed |

## Check a call

Set the secret, then pass the **raw body** and the headers to `verify_webhook`:

```python
fc = FazerCards(webhook_secret="your-webhook-secret")

event = fc.verify_webhook(raw_body, headers=request_headers)
```

or pass the signature yourself:

```python
event = fc.verify_webhook(raw_body, request_headers["X-Webhook-Signature"])
```

What is checked:

- A secret is configured. Otherwise `ConfigurationError`.
- The body is at most 256 KB. Larger bodies are refused before hashing.
- The signature is the HMAC SHA256 of the raw body with your secret, in hex. A `sha256=` prefix is optional and the hex may be in any case. The comparison runs in constant time.
- The body is a JSON object.

Any failure raises {py:class}`~fazercards_sdk.SignatureError`. Answer it with 401 and do nothing else.

:::{important}
Use the raw bytes of the request body, exactly as received. A body parsed to JSON and dumped again will not match the signature.
:::

`verify_webhook` makes no request and is a plain method on both the sync and the async client; it needs no `await`.

## The event

{py:class}`~fazercards_sdk.WebhookEvent`:

| Field | Meaning |
| --- | --- |
| `order_id` | The order the event is about |
| `status` | Its new `OrderStatus` |
| `order` | The full `Order`, when the body carried one |
| `merchant_txn_id` | A merchant transaction id, when present |
| `event` | The event name, when present |
| `raw` | The whole body |
| `needs_lookup` | `True` when the body has an order id but not a full order or a known status |

FazerCards bodies come in a few shapes (the order at the top level, under `order`, under `data`, or under `order.order`); all are read the same way.

When `needs_lookup` is `True`, read the order:

```python
order = fc.orders.get(event.order_id) if event.needs_lookup else event.order
```

## A FastAPI endpoint

```python
from fastapi import FastAPI, HTTPException, Request

from fazercards_sdk import AsyncFazerCards, SignatureError

app = FastAPI()
fazercards = AsyncFazerCards()


@app.post("/webhook/fazercards")
async def fazercards_webhook(request: Request) -> dict:
    try:
        event = fazercards.verify_webhook(await request.body(), headers=request.headers)
    except SignatureError:
        raise HTTPException(status_code=401) from None
    order = await fazercards.orders.get(event.order_id) if event.needs_lookup else event.order
    if order is None:
        return {"message": "OK"}
    if order.delivered and not order.awaiting_codes:
        await deliver(order.id, order.codes)
    elif order.failed:
        await refund(order.id, order.fail_reason)
    return {"message": "OK"}
```

This is [examples/fastapi_webhook.py](https://github.com/qiyascc/fazercards-python-sdk/blob/main/examples/fastapi_webhook.py) from the repository. A Django version is in [the Django checkout example](../examples/django-checkout.md).

## Handle each event once

FazerCards may deliver the same event more than once, for example after your server answered slowly. Make the handler idempotent: store which orders you have delivered and do nothing for an order that is already done.

## Without the client

The module functions work without an API key, for a small service that only receives webhooks:

```python
from fazercards_sdk import SIGNATURE_HEADER, verify_webhook

event = verify_webhook("your-webhook-secret", raw_body, headers[SIGNATURE_HEADER])
```

`fazercards_sdk.webhooks.sign(secret, body)` makes a signature, which is handy in tests.
