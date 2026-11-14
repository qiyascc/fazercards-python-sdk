# Quickstart

This walk through tops up a Free Fire account with 110 diamonds. It assumes the SDK is installed ([Installation](installation.md)) and that `FAZERCARDS_API_KEY` is set ([API key](api-key.md)).

## 1. Check the balance

```python
from fazercards_sdk import FazerCards

fc = FazerCards()
balance = fc.balance()
print(balance.amount, balance.currency)
```

`balance.amount` is a `Decimal`. Orders are paid from this balance.

## 2. Find the game

Top-up games are categories. List them all:

```python
for category in fc.topups.all_categories():
    print(category.category_id, category.name)
```

Category ids are short names such as `free_fire_cis`.

## 3. Read the offers

```python
offers = fc.topups.offers("free_fire_cis")
for offer in offers.offers:
    print(offer.id, offer.name, offer.price)
for field in offers.fields:
    print("needs", field.key, field.label, "required" if field.required else "optional")
```

`offers.offers` are the packages you can buy, with prices in USD as `Decimal`. `offers.fields` are the details the order needs, usually the player id and sometimes a server id.

```python
diamonds = offers.get("110_diamonds")
print(diamonds.name, diamonds.price)
```

## 4. Check the player id

```python
check = fc.topups.validate("free_fire", "123456789")
print(check.valid, check.player_name, check.region)
```

For games FazerCards can look up, `validate` tells you whether the id exists and whose it is, before you spend money. `fc.topups.validation_games()` lists those games. Note that the validation category (`free_fire`) can differ from the offer category (`free_fire_cis`).

## 5. Place the order

```python
order = fc.topups.order(
    "free_fire_cis",
    "110_diamonds",
    "123456789",
    idempotency_key="ORDER-1042",
)
print(order.id, order.status, order.total)
```

- `free_fire_cis` is the category and `110_diamonds` the offer.
- `123456789` is the player id.
- `idempotency_key` is your own order number. If the same key is sent again, FazerCards returns the first order instead of charging twice. Always pass one; see [Idempotency](../guides/idempotency.md).

## 6. Follow the order

A top-up usually starts as `created` or `processing`:

```python
final = fc.orders.wait(order.id, timeout=120, interval=5)
if final.delivered:
    print("done")
elif final.failed:
    print("failed:", final.fail_reason)
```

`wait` reads the order every `interval` seconds until it is delivered or failed, and returns it. After `timeout` seconds it raises `WaitTimeoutError` with the last read in `exc.order`.

In a shop, prefer a [webhook](../guides/webhooks.md) to waiting: FazerCards calls you when the order changes.

## 7. Close the client

```python
fc.close()
```

or use `with FazerCards() as fc:`.

## The whole script

```python
from fazercards_sdk import FazerCards, OutcomeUnknownError, WaitTimeoutError


def top_up(player_id: str, shop_order: str) -> None:
    with FazerCards() as fc:
        check = fc.topups.validate("free_fire", player_id)
        if check.valid is False:
            print("No such player")
            return
        try:
            order = fc.topups.order("free_fire_cis", "110_diamonds", player_id, idempotency_key=shop_order)
        except OutcomeUnknownError as exc:
            print("No answer. Look the order up before trying again. Key:", exc.idempotency_key)
            return
        try:
            order = fc.orders.wait(order.id)
        except WaitTimeoutError as exc:
            order = exc.order
        print(order.id, order.status, order.fail_reason or "")


if __name__ == "__main__":
    top_up("123456789", "ORDER-1042")
```

## The same with async

```python
import asyncio

from fazercards_sdk import AsyncFazerCards


async def main() -> None:
    async with AsyncFazerCards() as fc:
        balance, games = await asyncio.gather(fc.balance(), fc.topups.all_categories())
        print(balance.amount, len(games))


asyncio.run(main())
```
