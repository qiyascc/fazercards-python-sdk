# Top-ups

A top-up credits game currency (diamonds, UC, gems) straight to a player's account. You need the category, the offer, and the details that identify the player.

## Check the player first

```python
check = fc.topups.validate("free_fire", "123456789")
if check.valid:
    print("Player:", check.player_name, check.region)
```

`validate(category_id, player_id=None, *, server_id=None, fields=None)` asks FazerCards whether the player exists, before any money is spent. It returns a {py:class}`~fazercards_sdk.PlayerCheck`:

| Field | Meaning |
| --- | --- |
| `valid` | `True`, `False`, or `None` when FazerCards gave no verdict |
| `category_id`, `player_id` | What was checked |
| `player_name` | The in-game name, when FazerCards knows it |
| `region` | The player's region, when known |

Not every game supports the check. The ones that do, with the fields each needs:

```python
for game in fc.topups.validation_games():
    print(game.category_id, game.name, [f.key for f in game.fields])
```

The validation category can be different from the offer category. In the README example the check uses `free_fire` and the order uses `free_fire_cis`.

## Order

```python
order = fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="ORDER-1042")
```

| Argument | Meaning |
| --- | --- |
| `category_id` | The top-up category |
| `offer_id` | The offer, from `offers()` |
| `player_id` | The player id, for games that need one |
| `server_id` | The server or zone id, for games that need one |
| `fields` | Any other fields as a dict, merged with `player_id` and `server_id` |
| `idempotency_key` | Your order number. Strongly recommended, see [Idempotency](idempotency.md) |

Field values are sent as text. A missing field set, a nested value or a `None` raises `InvalidRequestError` before sending.

Games with a server:

```python
fc.topups.order("mobile_legends", "86_diamonds", "12345678", server_id="1234", idempotency_key="ORDER-1043")
```

Games with other fields:

```python
fc.topups.order("some_game", "offer", fields={"player_id": "123", "nickname": "abc"}, idempotency_key="ORDER-1044")
```

Category, offer and field names here are examples. Use the ids from your own catalog.

## What comes back

An {py:class}`~fazercards_sdk.Order`. A top-up usually comes back `created` or `processing` and moves on to `completed`, or to `failed` or `refund` with `fail_reason`. Follow it with a [webhook](webhooks.md) or with `fc.orders.wait(order.id)`; see [Orders](orders.md).

The returned order carries the key it was sent with, in `order.idempotency_key`.

## Safety

- The order is sent once. A timeout, a cut connection or a 5xx raises `OutcomeUnknownError`, which carries `idempotency_key`. Look the order up before trying again, or send it again with the **same** key.
- If FazerCards answers a reused key with an order for another category, offer or player, `KeyCollisionError` is raised instead of returning that order as yours.
