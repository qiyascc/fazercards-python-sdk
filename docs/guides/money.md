# Money

Every amount in the SDK is a `decimal.Decimal`. Floats cannot hold most decimal fractions exactly, and a shop that adds up `0.1 + 0.2` in floats ends up a fraction of a cent off. Decimals do not.

## Amounts you receive

Prices, totals, balances, rates and quotes are parsed from FazerCards' text into `Decimal` without passing through a float:

| Where | Field |
| --- | --- |
| `Offer` | `price` |
| `Order` | `unit_price`, `total` |
| `Balance` | `amount` |
| `Account` | `total_spent` |
| `StarsQuote` | `price_per_star`, `price(quantity)` |
| `PremiumPlan` | `price` |
| `SteamRates` | `rates`, `convert(...)` |

A value FazerCards sends that is not a number comes back as `None` rather than a wrong number.

## Amounts you send

Only the Steam order takes an amount. It accepts a `Decimal`, an `int`, a `float` or text, and checks it before sending:

| Given | Result |
| --- | --- |
| `Decimal("19.50")`, `"19.5"`, `19.5`, `20` | Sent as `19.50`, `19.50`, `19.50`, `20.00` |
| `Decimal("1.005")` | `InvalidRequestError`: more than two decimal places |
| `0`, `-5` | `InvalidRequestError`: must be greater than zero |
| `True` | `InvalidRequestError`: must be a number |
| `"abc"`, `float("nan")`, `float("inf")` | `InvalidRequestError` |

Pass a `Decimal` or text when you can. A float like `19.99` is converted through its text form, which works, but it is better not to have the float in the first place.

## Your own margins

Keep your shop's arithmetic in `Decimal` too:

```python
from decimal import ROUND_HALF_UP, Decimal

MARGIN = Decimal("1.12")

offer = fc.giftcards.cards("playstation_tr").get("250_try")
sell_price = (offer.price * MARGIN).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```
