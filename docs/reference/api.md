# API reference

Generated from the code. The code has no docstrings; the guides explain each part and this page lists every public class, method and argument. Import from the top level package: `from fazercards_sdk import FazerCards, OrderStatus, KeyCollisionError`. Resource classes are reached through a client as `fc.topups`, `fc.giftcards`, `fc.orders`, `fc.telegram`, `fc.steam` and `fc.account`.

## Clients

See [Quickstart](../getting-started/quickstart.md) and [Async](../guides/async.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.FazerCards
   :members: balance, verify_webhook, request, close

.. autoclass:: fazercards_sdk.AsyncFazerCards
   :members: balance, verify_webhook, request, close
```

| Constructor argument | Meaning |
| --- | --- |
| `api_key` | The reseller API key. Required here or in the settings |
| `settings` | A ready `Settings` object |
| `config_file` | Path of a config file |
| `http_client` | Your own `httpx.Client` or `httpx.AsyncClient` |
| any setting | Such as `webhook_secret="..."` or `timeout=20` |

Attributes: `settings`, `rate_limit` (the last `RateLimit` seen, or `None`).

## `fc.topups`

See [Catalog](../guides/catalog.md) and [Top-ups](../guides/topups.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.Topups
   :members: categories, all_categories, offers, validation_games, validate, order
```

## `fc.giftcards`

See [Gift cards](../guides/giftcards.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.GiftCards
   :members: categories, all_categories, offers, cards, order
```

## `fc.orders`

See [Orders](../guides/orders.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.Orders
   :members: get, list, recent, wait
```

## `fc.telegram`

See [Telegram](../guides/telegram.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.Telegram
   :members: stars_quote, premium_quote, buy_stars, buy_premium
```

## `fc.steam`

See [Steam](../guides/steam.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.Steam
   :members: rates, check_login, order
```

## `fc.account`

See [Account](../guides/account.md).

```{eval-rst}
.. autoclass:: fazercards_sdk.resources.AccountResource
   :members: me, balance, webhook, set_webhook
```

## Webhooks

See [Webhooks](../guides/webhooks.md).

```{eval-rst}
.. autofunction:: fazercards_sdk.verify_webhook
.. autofunction:: fazercards_sdk.parse_webhook
.. autofunction:: fazercards_sdk.webhooks.sign
.. autofunction:: fazercards_sdk.webhooks.matches
```

`SIGNATURE_HEADER` is `"X-Webhook-Signature"`.

## Settings

See [Configuration](../getting-started/configuration.md).

```{eval-rst}
.. autofunction:: fazercards_sdk.load_settings

.. autoclass:: fazercards_sdk.Settings
   :members: key, scoped, path, url, resolved_user_agent, check_transport
   :undoc-members: false

.. autoclass:: fazercards_sdk.Endpoints
   :members:
   :undoc-members: false
```

## Messages

```{eval-rst}
.. autofunction:: fazercards_sdk.messages.use
.. autofunction:: fazercards_sdk.messages.reset
.. autofunction:: fazercards_sdk.messages.catalog
.. autofunction:: fazercards_sdk.messages.text
```

## Errors

See [Errors](../guides/errors.md).

```{eval-rst}
.. autoexception:: fazercards_sdk.FazerCardsError
.. autoexception:: fazercards_sdk.ConfigurationError
.. autoexception:: fazercards_sdk.InvalidRequestError
.. autoexception:: fazercards_sdk.SignatureError
.. autoexception:: fazercards_sdk.KeyCollisionError
.. autoexception:: fazercards_sdk.WaitTimeoutError
.. autoexception:: fazercards_sdk.TransportError
.. autoexception:: fazercards_sdk.NotSentError
.. autoexception:: fazercards_sdk.OutcomeUnknownError
.. autoexception:: fazercards_sdk.APIError
.. autoexception:: fazercards_sdk.BadRequestError
.. autoexception:: fazercards_sdk.AuthenticationError
.. autoexception:: fazercards_sdk.NotFoundError
.. autoexception:: fazercards_sdk.ConflictError
.. autoexception:: fazercards_sdk.RateLimitError
.. autoexception:: fazercards_sdk.ServerError
```
