# FazerCards Python SDK

A typed Python client for the FazerCards reseller API: game top-ups, gift cards, Telegram Stars and Premium, Steam wallet top-ups, orders and signed webhooks. There is a sync client, `FazerCards`, and an async one, `AsyncFazerCards`, with the same methods. Every order carries an idempotency key and the retry rules are built so an order is never placed twice.

```python
from fazercards_sdk import FazerCards

with FazerCards("API_KEY") as fc:
    check = fc.topups.validate("free_fire", "123456789")
    if check.valid:
        order = fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="ORDER-1042")
        print(order.id, order.status, order.total)
```

## Where to go next

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: getting-started/installation
:link-type: doc

Python versions, a virtual environment step by step, pip, uv and Poetry.
:::

:::{grid-item-card} API key
:link: getting-started/api-key
:link-type: doc

Where the key goes and how to keep it out of the code.
:::

:::{grid-item-card} Quickstart
:link: getting-started/quickstart
:link-type: doc

Balance, catalog, a top-up and its status, in one short script.
:::

:::{grid-item-card} Idempotency
:link: guides/idempotency
:link-type: doc

How order keys stop double purchases, and what to do with an unknown outcome.
:::

:::{grid-item-card} Gift cards
:link: guides/giftcards
:link-type: doc

Ordering cards and getting the codes, including codes that arrive late.
:::

:::{grid-item-card} Webhooks
:link: guides/webhooks
:link-type: doc

Signature checks, payload shapes and a FastAPI endpoint.
:::

:::{grid-item-card} Examples
:link: examples/index
:link-type: doc

A webhook endpoint, a Django checkout, a price list, a balance alert, a reconcile job.
:::

:::{grid-item-card} API reference
:link: reference/api
:link-type: doc

Every class, method and field.
:::

::::

## What the SDK takes care of

- **No double purchases.** Every top-up, gift card and Steam order sends an `Idempotency-Key`. Pass your own order number and a double click or a crash cannot buy twice. Orders are never resent after an ambiguous failure, unless you ask for exactly one resend with the same key.
- **Collisions are caught.** A reused key that returns an order for another item raises `KeyCollisionError`, never a false success.
- **Late gift card codes.** FazerCards can mark a gift card order completed before the codes are attached. The client reads the order again and flags it when the codes are still missing.
- **Money is exact.** Prices and totals are `Decimal` end to end, and amounts with more than two decimals are refused.
- **Signed webhooks.** HMAC SHA256 signatures are checked in constant time, with a size limit on the body.
- **Checks before sending.** Quantities, months, usernames, amounts, ids and URLs are checked locally.
- **Typed results** as frozen dataclasses, with the raw answer kept in `.raw`.

```{toctree}
:hidden:
:caption: Getting started

getting-started/installation
getting-started/api-key
getting-started/quickstart
getting-started/configuration
```

```{toctree}
:hidden:
:caption: Guides

guides/catalog
guides/topups
guides/giftcards
guides/telegram
guides/steam
guides/orders
guides/idempotency
guides/webhooks
guides/account
guides/money
guides/async
guides/errors
guides/safety
guides/messages
guides/advanced
guides/testing
```

```{toctree}
:hidden:
:caption: Examples

examples/index
examples/fastapi-webhook
examples/django-checkout
examples/price-list
examples/balance-alert
examples/reconcile
```

```{toctree}
:hidden:
:caption: Reference

reference/api
reference/models
reference/changelog
reference/faq
```

```{toctree}
:hidden:
:caption: Project

project/development
project/about
```
