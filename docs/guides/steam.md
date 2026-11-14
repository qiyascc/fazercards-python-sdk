# Steam wallet

FazerCards tops up a Steam wallet by login, in USD, RUB, UAH or KZT.

## Rates

```python
from decimal import Decimal

rates = fc.steam.rates()
print(rates.base, rates.rates, rates.updated_at)
print(rates.convert(Decimal("10"), "RUB"))
```

{py:class}`~fazercards_sdk.SteamRates` has `base` (the base currency, `USD`), `rates` (a dict of currency to `Decimal` rate) and `updated_at`. `convert(usd, currency)` multiplies a USD amount by the rate, or returns `None` for an unknown currency.

## Check the login

```python
check = fc.steam.check_login("steam_login")
if check.valid:
    print("can be topped up")
elif check.valid is None:
    print("FazerCards could not verify the login")
else:
    print("this login cannot be topped up")
```

{py:class}`~fazercards_sdk.SteamLogin` has `can_refill` and `unverified`. Its `valid` property reads them as three answers:

| `valid` | Meaning |
| --- | --- |
| `True` | `can_refill` is `True` |
| `None` | FazerCards could not verify the login, or did not say |
| `False` | FazerCards says the login cannot be refilled |

## Order

```python
from decimal import Decimal

from fazercards_sdk import SteamCurrency

order = fc.steam.order("steam_login", Decimal("19.50"), SteamCurrency.USD, idempotency_key="ORDER-1044")
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `login` | | The Steam login |
| `amount` | | The amount, in `currency` |
| `currency` | `USD` | `USD`, `RUB`, `UAH` or `KZT`, as `SteamCurrency` or text in any case |
| `idempotency_key` | random | Your order number |

The amount can be a `Decimal`, an `int`, a `float` or text, and must be positive with at most two decimal places. It is always sent with two decimals, so `19.5` goes out as `19.50`. `1.005`, `0`, `-5`, `True` or `"abc"` raise `InvalidRequestError` before sending. See [Money](money.md).

## Safety

A timeout or a 5xx raises `OutcomeUnknownError` with the key; look the order up or resend with the same key. Steam orders are not checked for key collisions, because the answer does not echo the login and amount; use a unique key per purchase.
