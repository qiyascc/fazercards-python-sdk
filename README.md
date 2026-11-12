# fazercards-python-sdk

[![PyPI](https://img.shields.io/pypi/v/fazercards-python-sdk?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/fazercards-python-sdk/)
[![Python](https://img.shields.io/badge/python-3.10%20to%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FazerCards](https://img.shields.io/badge/api-FazerCards%20v2-7C3AED)](https://api.fzr.cards/api/v2)
[![Typed](https://img.shields.io/badge/typing-mypy-2A6DB2)](https://mypy-lang.org)
[![Async](https://img.shields.io/badge/sync%20%2B%20async-httpx-5A45FF)](https://www.python-httpx.org)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/qiyascc/fazercards-python-sdk/blob/main/LICENSE)

Typed Python client for the FazerCards reseller API. Game top-ups, gift cards, Telegram Stars and Premium, Steam wallet, orders and signed webhooks. Sync and async, with retry rules built so an order is never placed twice.

```bash
pip install fazercards-python-sdk
```

## Top up a game

```python
from fazercards_sdk import FazerCards

with FazerCards("API_KEY") as fc:
    check = fc.topups.validate("free_fire", "123456789")
    if check.valid:
        order = fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="ORDER-1042")
```

`order.status` moves from `created` to `processing` to `completed`, or to `failed` / `refund` with `order.fail_reason`. Follow it by webhook, or with `fc.orders.wait(order.id)`.

## Sell a gift card

```python
order = fc.giftcards.order("playstation_tr", "250_try", quantity=1, idempotency_key="ORDER-1043")
order.codes
```

FazerCards can answer a gift card order with `completed` and an empty `cards` list, then fill the list a moment later. The client reads the order again before it returns (`code_checks`, default 3). If the codes still have not arrived, `order.awaiting_codes` is `True`: keep the order open and read it later, never show the customer an empty result.

## Telegram and Steam

```python
fc.telegram.stars_quote().price(500)
fc.telegram.buy_stars("@username", 500)
fc.telegram.buy_premium("username", months=12)

if fc.steam.check_login("steam_login").valid:
    fc.steam.order("steam_login", "19.50", "USD", idempotency_key="ORDER-1044")
```

## Catalog

```python
games = fc.topups.all_categories()
cards = fc.giftcards.all_categories()
offers = fc.topups.offers("free_fire_cis")
offers.get("110_diamonds").price
offers.fields
fc.giftcards.cards("playstation_tr").offers[0].stock
```

Categories come in cursor pages of up to 500 (`fc.topups.categories(limit, cursor)`); `all_categories()` follows the cursor. Orders come in numbered pages of up to 100 (`fc.orders.list(page, limit)`, `fc.orders.recent(count)`).

## Webhooks

```python
event = fc.verify_webhook(request.body, headers=request.headers)
if event.needs_lookup:
    order = fc.orders.get(event.order_id)
```

The body is checked against `X-Webhook-Signature` (HMAC SHA256 of the raw body, `sha256=` prefix optional) in constant time. Set the address with `fc.account.set_webhook("https://shop.example/webhook/fazercards")`. See [examples/fastapi_webhook.py](https://github.com/qiyascc/fazercards-python-sdk/blob/main/examples/fastapi_webhook.py).

## Safety

| Situation | What the client does |
| --- | --- |
| Connection refused, nothing sent | Retries, then `NotSentError` |
| Timeout, cut connection or 5xx on an order | No retry, `OutcomeUnknownError` with the `idempotency_key` |
| Same failure on a read | Retries with backoff, then `TransportError` |
| 429 | Waits `Retry-After` and retries, the request was not processed |
| `resend_keyed_orders=True` | An order with an Idempotency-Key is resent once with the same key |
| Telegram purchase | Takes no key on the API side, so it is never resent |
| Reused key that returns another item | `KeyCollisionError`, never counted as success |
| Gift card `completed` without codes | Read again, then `order.awaiting_codes` |
| Quantity, months, amount like `1.005` or `True` | `InvalidRequestError` before anything is sent |
| `base_url` over plain http | `ConfigurationError`, except localhost or `allow_insecure_http` |
| Webhook body over 256 KB | Rejected before hashing |

Every top-up, gift card and Steam order carries an `Idempotency-Key`. Pass your own order number, so a double click or a crash can not buy twice. With several shops on one account set `idempotency_prefix`. Prices are `Decimal` end to end. `fc.rate_limit` keeps the last `X-RateLimit-*` headers.

## Endpoints

| Namespace | Methods |
| --- | --- |
| `topups` | `categories` `all_categories` `offers` `validation_games` `validate` `order` |
| `giftcards` | `categories` `all_categories` `cards` `order` |
| `orders` | `get` `list` `recent` `wait` |
| `telegram` | `stars_quote` `premium_quote` `buy_stars` `buy_premium` |
| `steam` | `rates` `check_login` `order` |
| `account` | `me` `balance` `webhook` `set_webhook` |
| client | `balance` `verify_webhook` `request` |

`AsyncFazerCards` has the same methods, awaited.

## Errors

`FazerCardsError` is the base. API answers raise `APIError` subclasses by status: `BadRequestError` (400), `AuthenticationError` (401, 403), `NotFoundError` (404), `ConflictError` (409), `RateLimitError` (429), `ServerError` (5xx). Each carries `status_code`, `message` and the raw `body`.

## Config

Pass values in code, or set `FAZERCARDS_API_KEY`, `FAZERCARDS_WEBHOOK_SECRET`, `FAZERCARDS_BASE_URL`, `FAZERCARDS_IDEMPOTENCY_PREFIX`, `FAZERCARDS_TIMEOUT`, `FAZERCARDS_MAX_RETRIES`, or put them in `fazercards.toml` ([example](https://github.com/qiyascc/fazercards-python-sdk/blob/main/examples/fazercards.toml)). Every path is a setting (`FAZERCARDS_ENDPOINTS__BALANCE=...`). Messages live in `messages.yaml` and can be replaced with `messages.use(...)`.

## Develop

```bash
pip install -e ".[dev]" && pytest && ruff check . && mypy src
```

## Links

- Source code: [github.com/qiyascc/fazercards-python-sdk](https://github.com/qiyascc/fazercards-python-sdk)
- PyPI: [pypi.org/project/fazercards-python-sdk](https://pypi.org/project/fazercards-python-sdk/)
- Project page: [theqiyas.cc/projects/fazercards-sdk](https://theqiyas.cc/projects/fazercards-sdk/)
- Author: [Qiyas Sadıqov](https://theqiyas.cc), more projects at [theqiyas.cc](https://theqiyas.cc)

## License

MIT
