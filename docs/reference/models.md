# Models and enums

Everything the SDK returns is a frozen dataclass. Money is `Decimal`, times are timezone aware `datetime` objects, and models built from FazerCards answers keep the original in `.raw`, left out of `repr()` and equality.

| Model | Returned by | Guide |
| --- | --- | --- |
| `Balance` | `balance`, `account.balance` | [Account](../guides/account.md) |
| `Account` | `account.me` | [Account](../guides/account.md#account-details) |
| `Webhook` | `account.webhook`, `set_webhook` | [Webhooks](../guides/webhooks.md) |
| `CategoryPage`, `Category` | `categories`, `all_categories` | [Catalog](../guides/catalog.md) |
| `Offers`, `Offer`, `InputField` | `offers`, `cards` | [Catalog](../guides/catalog.md#offers) |
| `ValidationGame` | `topups.validation_games` | [Top-ups](../guides/topups.md) |
| `PlayerCheck` | `topups.validate` | [Top-ups](../guides/topups.md) |
| `Order`, `StatusChange` | every order call, `orders.get`, `wait` | [Orders](../guides/orders.md) |
| `OrderPage` | `orders.list` | [Orders](../guides/orders.md#list-orders) |
| `StarsQuote`, `PremiumQuote`, `PremiumPlan` | `telegram.*_quote` | [Telegram](../guides/telegram.md) |
| `SteamRates`, `SteamLogin` | `steam.rates`, `steam.check_login` | [Steam](../guides/steam.md) |
| `WebhookEvent` | `verify_webhook`, `parse_webhook` | [Webhooks](../guides/webhooks.md#the-event) |
| `RateLimit` | `fc.rate_limit` | [Account](../guides/account.md#rate-limits) |

```{eval-rst}
.. autoclass:: fazercards_sdk.Balance
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.Account
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.Webhook
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.CategoryPage
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.Category
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.Offers
   :members: get
   :undoc-members: false
.. autoclass:: fazercards_sdk.Offer
   :members: in_stock
   :undoc-members: false
.. autoclass:: fazercards_sdk.InputField
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.ValidationGame
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.PlayerCheck
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.Order
   :members: delivered, failed, in_flight, awaiting_codes, with_key
   :undoc-members: false
.. autoclass:: fazercards_sdk.StatusChange
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.OrderPage
   :members: has_more
   :undoc-members: false
.. autoclass:: fazercards_sdk.StarsQuote
   :members: price
   :undoc-members: false
.. autoclass:: fazercards_sdk.PremiumQuote
   :members: plan
   :undoc-members: false
.. autoclass:: fazercards_sdk.PremiumPlan
   :members:
   :undoc-members: false
.. autoclass:: fazercards_sdk.SteamRates
   :members: convert
   :undoc-members: false
.. autoclass:: fazercards_sdk.SteamLogin
   :members: valid
   :undoc-members: false
.. autoclass:: fazercards_sdk.WebhookEvent
   :members: needs_lookup
   :undoc-members: false
.. autoclass:: fazercards_sdk.RateLimit
   :members:
   :undoc-members: false
```

## Enums and constants

| Name | Values |
| --- | --- |
| `OrderStatus` | `created`, `pending`, `processing`, `completed`, `delivered`, `success`, `failed`, `refund`, `refunded`, `cancelled`, `canceled`, `error`, `unknown`. Properties `delivered`, `failed`, `in_flight`, `final` |
| `OrderKind` | `topup`, `gift_card`, `telegram_stars`, `telegram_premium`, `steam_topup`, `unknown` |
| `SteamCurrency` | `USD`, `RUB`, `UAH`, `KZT` |
| `PREMIUM_MONTHS` | `(3, 6, 12)` |
| `SIGNATURE_HEADER` | `"X-Webhook-Signature"` |

```{eval-rst}
.. autoclass:: fazercards_sdk.OrderStatus
   :members: delivered, failed, in_flight, final, of
   :undoc-members:
   :member-order: bysource
.. autoclass:: fazercards_sdk.OrderKind
   :members: of
   :undoc-members:
   :member-order: bysource
.. autoclass:: fazercards_sdk.SteamCurrency
   :members:
   :undoc-members:
   :member-order: bysource
```
