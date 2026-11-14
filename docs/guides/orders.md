# Orders

Every purchase, whatever its kind, becomes an {py:class}`~fazercards_sdk.Order`.

## Read one order

```python
order = fc.orders.get("ord-1001")
print(order.kind, order.status, order.total, order.codes)
```

The id is checked only for being non empty and having no `/` or `?`; the format is left to FazerCards.

## The order object

| Field | Meaning |
| --- | --- |
| `id` | The FazerCards order id |
| `kind` | `OrderKind`: `topup`, `gift_card`, `telegram_stars`, `telegram_premium`, `steam_topup` or `unknown` |
| `status` | `OrderStatus`, see below |
| `title` | A one line description from FazerCards |
| `category_id`, `category_name` | The category |
| `offer_id`, `offer_name` | The offer or card |
| `quantity` | Units, stars or months, depending on the kind |
| `fields` | The player fields sent with a top-up |
| `unit_price`, `total` | Prices in USD as `Decimal` |
| `codes` | Gift card codes, as text |
| `fail_reason` | Why a failed order failed |
| `history` | A tuple of `StatusChange(status, at)` |
| `created_at`, `completed_at` | Timestamps |
| `idempotency_key` | The key the SDK sent, on orders it placed |
| `raw` | The whole order |

Shortcuts:

| Property | `True` when |
| --- | --- |
| `delivered` | The status is `completed`, `delivered` or `success` |
| `failed` | The status is `failed`, `refund`, `refunded`, `cancelled`, `canceled` or `error` |
| `in_flight` | The status is `created`, `pending` or `processing` |
| `awaiting_codes` | A gift card order is delivered but has no codes yet |

## Statuses

FazerCards uses several spellings; the SDK accepts all of them in `OrderStatus`:

| Group | Statuses |
| --- | --- |
| In flight | `CREATED`, `PENDING`, `PROCESSING` |
| Delivered | `COMPLETED`, `DELIVERED`, `SUCCESS` |
| Failed | `FAILED`, `REFUND`, `REFUNDED`, `CANCELLED`, `CANCELED`, `ERROR` |
| Other | `UNKNOWN` for anything new |

`OrderStatus` is a string enum and `str(status)` is the lower case value, such as `completed`. `status.final` is `True` for delivered and failed statuses.

A usual flow: `created`, then `processing`, then `completed`; or `failed` / `refund` with `fail_reason`.

## List orders

```python
page = fc.orders.list(page=1, limit=50)
for order in page.items:
    print(order.id, order.status, order.total)
print(page.total, page.has_more)
```

`list(page=1, limit=20)` reads one numbered page, up to 100 per page. {py:class}`~fazercards_sdk.OrderPage` has `items`, `total`, `page`, `limit` and `has_more`.

`recent(count=100)` reads pages until it has `count` orders or runs out, and returns a tuple, in the order FazerCards lists them:

```python
last_200 = fc.orders.recent(200)
```

## Wait for an order

```python
from fazercards_sdk import WaitTimeoutError

try:
    final = fc.orders.wait("ord-1002", timeout=120, interval=5)
except WaitTimeoutError as exc:
    final = exc.order
```

`wait(order_id, timeout=120, interval=5)` reads the order every `interval` seconds until it is final and, for gift cards, has its codes. After `timeout` seconds it raises `WaitTimeoutError`, carrying the last read in `.order`.

Waiting holds a worker for the whole time. In a shop, a [webhook](webhooks.md) is the better way to learn that an order finished.
