# Account

## Balance

```python
balance = fc.balance()
print(balance.amount, balance.currency)
```

`fc.balance()` is the same as `fc.account.balance()`. {py:class}`~fazercards_sdk.Balance` has `amount` (a `Decimal`, `0` when FazerCards sends none), `currency` (`USD` unless FazerCards says otherwise) and `raw`.

Check the balance before a large gift card order, or alert yourself when it runs low; see [the balance alert example](../examples/balance-alert.md).

## Account details

```python
me = fc.account.me()
print(me.login, me.email, me.plan, me.plan_expires_at, me.total_orders, me.total_spent)
```

{py:class}`~fazercards_sdk.Account`:

| Field | Meaning |
| --- | --- |
| `login`, `email` | The reseller account |
| `plan` | The reseller plan |
| `plan_expires_at` | When the plan ends |
| `plan_auto_renew` | Whether it renews |
| `subscription_active` | Whether the subscription is active |
| `total_spent` | USD spent, a `Decimal` |
| `total_orders` | Orders placed |
| `created_at`, `last_active_at` | Timestamps |

## Webhook settings

`fc.account.webhook()` and `fc.account.set_webhook(url)`; see [Webhooks](webhooks.md#set-the-address).

## Rate limits

FazerCards reports its limits in `X-RateLimit-*` headers. The client keeps the last ones it saw:

```python
fc.balance()
if fc.rate_limit:
    print(fc.rate_limit.limit, fc.rate_limit.remaining, fc.rate_limit.reset)
```

`fc.rate_limit` is a {py:class}`~fazercards_sdk.RateLimit` with `limit`, `remaining` and `reset`, or `None` before the first answer that carried the headers. A 429 is handled for you: the client waits for `Retry-After` (or the reset time) and tries again.
