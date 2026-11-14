# Configuration

Only the API key is required. Everything else has a default, and every setting can come from code, the environment or a config file, loaded with [goodconf](https://github.com/lincolnloop/goodconf).

## Where settings come from

1. **Arguments in code**, such as `FazerCards(timeout=10)`. Highest priority.
2. **Environment variables** starting with `FAZERCARDS_`.
3. **A config file**, such as `fazercards.toml`.
4. **The defaults** below.

## In code

```python
from fazercards_sdk import FazerCards

fc = FazerCards("API_KEY", webhook_secret="SECRET", idempotency_prefix="shop-a", timeout=20)
```

Shared settings:

```python
from fazercards_sdk import FazerCards, load_settings

settings = load_settings("/etc/shop/fazercards.toml")
fc = FazerCards(settings=settings)
```

## Environment variables

```bash
export FAZERCARDS_API_KEY=your-api-key
export FAZERCARDS_WEBHOOK_SECRET=your-webhook-secret
export FAZERCARDS_IDEMPOTENCY_PREFIX=shop-a
```

Windows CMD:

```bat
set FAZERCARDS_API_KEY=your-api-key
set FAZERCARDS_IDEMPOTENCY_PREFIX=shop-a
```

Nested settings use a double underscore: `FAZERCARDS_ENDPOINTS__BALANCE=/balance`.

## Config file

`fazercards.toml`, `fazercards.yaml`, `fazercards.yml` or `fazercards.json` in the working directory, or the file named in `FAZERCARDS_CONFIG` or `config_file=`:

::::{tab-set}

:::{tab-item} TOML
```toml
api_key = "your-api-key"
webhook_secret = "your-webhook-secret"
idempotency_prefix = "shop"
timeout = 30
max_retries = 2
```
:::

:::{tab-item} YAML
```yaml
api_key: your-api-key
webhook_secret: your-webhook-secret
idempotency_prefix: shop
timeout: 30
max_retries: 2
```
:::

:::{tab-item} JSON
```json
{
  "api_key": "your-api-key",
  "webhook_secret": "your-webhook-secret",
  "idempotency_prefix": "shop",
  "timeout": 30,
  "max_retries": 2
}
```
:::

::::

The repository has this file as [examples/fazercards.toml](https://github.com/qiyascc/fazercards-python-sdk/blob/main/examples/fazercards.toml). Keep files with keys out of version control.

## All settings

| Setting | Environment variable | Default | What it does |
| --- | --- | --- | --- |
| `api_key` | `FAZERCARDS_API_KEY` | required | Reseller API key, sent as `X-API-Key` |
| `base_url` | `FAZERCARDS_BASE_URL` | `https://api.fzr.cards/api/v2` | API address, including the version path |
| `endpoints` | `FAZERCARDS_ENDPOINTS__<NAME>` | see below | Path of every call, relative to `base_url` |
| `webhook_secret` | `FAZERCARDS_WEBHOOK_SECRET` | empty | Secret used to check the `X-Webhook-Signature` header |
| `idempotency_prefix` | `FAZERCARDS_IDEMPOTENCY_PREFIX` | empty | Put in front of every Idempotency-Key, as `prefix:key`, to keep two shops on one account apart |
| `timeout` | `FAZERCARDS_TIMEOUT` | `30` | Seconds to wait for an answer |
| `connect_timeout` | `FAZERCARDS_CONNECT_TIMEOUT` | `10` | Seconds to wait for a connection |
| `max_retries` | `FAZERCARDS_MAX_RETRIES` | `2` | Extra attempts for calls that are safe to repeat, 0 to 10 |
| `backoff_base` | `FAZERCARDS_BACKOFF_BASE` | `0.5` | First wait between retries, in seconds |
| `backoff_cap` | `FAZERCARDS_BACKOFF_CAP` | `8` | Longest wait between retries, in seconds |
| `resend_keyed_orders` | `FAZERCARDS_RESEND_KEYED_ORDERS` | `false` | Resend an order once, with the same Idempotency-Key, after a timeout or a 5xx |
| `code_checks` | `FAZERCARDS_CODE_CHECKS` | `3` | Extra reads of a gift card order that came back completed without codes, 0 to 20 |
| `code_check_wait` | `FAZERCARDS_CODE_CHECK_WAIT` | `1` | Seconds between those reads |
| `user_agent` | `FAZERCARDS_USER_AGENT` | `fazercards-python-sdk/{version}` | User-Agent header |
| `allow_insecure_http` | `FAZERCARDS_ALLOW_INSECURE_HTTP` | `false` | Allow a plain http `base_url` outside localhost, for a private test server only |

## Endpoints

| Name | Default |
| --- | --- |
| `me` | `/me` |
| `balance` | `/balance` |
| `webhook` | `/account/webhook` |
| `topup_categories` | `/topups` |
| `topup_offers` | `/topups/offers` |
| `topup_order` | `/topups/order` |
| `validate_id` | `/topups/validate-id` |
| `giftcard_categories` | `/giftcards` |
| `giftcard_offers` | `/giftcards/cards` |
| `giftcard_order` | `/giftcards/order` |
| `orders` | `/orders` |
| `order` | `/orders/{order_id}` |
| `stars_quote` | `/telegram/stars` |
| `stars_buy` | `/telegram/stars/buy` |
| `premium_quote` | `/telegram/premium` |
| `premium_buy` | `/telegram/premium/buy` |
| `steam_rates` | `/steam-topup/rates` |
| `steam_login` | `/steam-topup/check-login` |
| `steam_order` | `/steam-topup/order` |

## Plain http

`base_url` must be https because the API key travels with every request. `localhost`, `127.0.0.1` and `::1` may use http. Anything else raises `ConfigurationError` unless `allow_insecure_http=True`.

## Your own httpx client

```python
import httpx

from fazercards_sdk import FazerCards

fc = FazerCards(http_client=httpx.Client(proxy="http://proxy.internal:3128", timeout=30))
```

`proxy=` needs httpx 0.26 or newer; older versions call it `proxies=`. A client you pass in is not closed by `fc.close()`. Use `httpx.AsyncClient` with `AsyncFazerCards`.
