# Telegram Stars and Premium

FazerCards can send Telegram Stars to a username and gift Telegram Premium for 3, 6 or 12 months.

## Prices

```python
stars = fc.telegram.stars_quote()
print(stars.price_per_star, stars.min_amount, stars.max_amount)
print(stars.price(500))

premium = fc.telegram.premium_quote()
for plan in premium.plans:
    print(plan.months, plan.price)
print(premium.plan(12))
```

{py:class}`~fazercards_sdk.StarsQuote`:

| Field or method | Meaning |
| --- | --- |
| `price_per_star` | USD per star, a `Decimal` |
| `min_amount`, `max_amount` | Allowed quantities |
| `rates_updated_at` | When FazerCards last updated the rate |
| `price(quantity)` | `price_per_star * quantity` |

{py:class}`~fazercards_sdk.PremiumQuote` has `plans`, a tuple of `PremiumPlan(months, price)`, `rates_updated_at`, and `plan(months)` which returns the plan or `None`.

## Buy Stars

```python
order = fc.telegram.buy_stars("@username", 500)
```

The username may start with `@`; it is sent without it. It must be 4 to 32 letters, digits or underscores. The quantity is a whole number from 50 to 100000. Anything else raises `InvalidRequestError` before sending.

## Buy Premium

```python
order = fc.telegram.buy_premium("username", months=12)
```

`months` is 3, 6 or 12.

## No idempotency key

The FazerCards API takes no Idempotency-Key on Telegram purchases. The SDK therefore treats them as the most fragile writes it has:

- They are never resent, not even with `resend_keyed_orders=True`.
- A timeout, a cut connection or a 5xx raises `OutcomeUnknownError` without a key.

After an unknown outcome, look at the recent orders before buying again:

```python
from fazercards_sdk import OrderKind, OutcomeUnknownError

try:
    order = fc.telegram.buy_stars("@username", 500)
except OutcomeUnknownError:
    recent = [o for o in fc.orders.recent(20) if o.kind is OrderKind.TELEGRAM_STARS]
    print([(o.id, o.status, o.quantity, o.created_at) for o in recent])
```

In your own shop, keep your order in a "pending" state until you have found the FazerCards order, so a customer is never charged twice.
