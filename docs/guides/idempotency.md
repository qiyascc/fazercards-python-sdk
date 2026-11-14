# Idempotency

Selling top-ups and gift cards means spending your balance on behalf of a customer. The worst bug in such a shop is buying twice: a double click, a retry after a timeout, a worker that crashed after paying but before saving. The FazerCards API protects against this with an **Idempotency-Key**, and the SDK uses it on every order that supports it.

## How it works

Every top-up, gift card and Steam order carries an `Idempotency-Key` header. FazerCards remembers the key: a second order with the same key does not buy again, it returns the order the first one created.

```python
order = fc.giftcards.order("playstation_tr", "250_try", idempotency_key="ORDER-1043")
again = fc.giftcards.order("playstation_tr", "250_try", idempotency_key="ORDER-1043")
assert again.id == order.id
```

## Use your own order number

If you pass no key, the SDK makes a random one for each call, which protects a single request but not your shop: a second call gets a new random key and buys again. **Pass your own order number**, the one in your database, so every attempt for that order sends the same key.

```python
def fulfil(shop_order_id: str, card_id: str):
    return fc.giftcards.order("playstation_tr", card_id, idempotency_key=f"order-{shop_order_id}")
```

Keys are up to 200 characters. The key the SDK sent is on the result, in `order.idempotency_key`, and on `OutcomeUnknownError` as `exc.idempotency_key`.

## Several shops on one account

Two shops that both number their orders from 1 would collide. Set `idempotency_prefix` per shop and every key is sent as `prefix:key`:

```python
fc = FazerCards(idempotency_prefix="shop-a")
fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="1042")
```

sends `Idempotency-Key: shop-a:1042`.

## When a key comes back with another item

If a key you reuse belongs to an order for a different item (another category, offer or player), FazerCards returns that old order. Treating it as success would hand a customer the wrong thing. The SDK compares the answer with what you asked for and raises {py:class}`~fazercards_sdk.KeyCollisionError` instead:

```python
from fazercards_sdk import KeyCollisionError

try:
    fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="1042")
except KeyCollisionError as exc:
    print("key", exc.idempotency_key, "is taken by", exc.order)
```

This check runs for top-ups (category, offer and player) and gift cards (category and card). Steam answers do not echo enough to compare, so give each Steam purchase a unique key.

## Unknown outcomes

A timeout, a cut connection or a 5xx on an order leaves you not knowing whether FazerCards placed it. The SDK never resends an order on its own. It raises {py:class}`~fazercards_sdk.OutcomeUnknownError`, which carries the key.

You then have two safe options:

1. **Resend with the same key.** If the first attempt went through, FazerCards returns that order; if not, it places it now. Either way you buy once.
2. **Look it up** with `fc.orders.recent()` and match on your data.

```python
from fazercards_sdk import OutcomeUnknownError

def order_card(shop_order_id: str):
    key = f"order-{shop_order_id}"
    try:
        return fc.giftcards.order("playstation_tr", "250_try", idempotency_key=key)
    except OutcomeUnknownError:
        return fc.giftcards.order("playstation_tr", "250_try", idempotency_key=key)
```

## Resending automatically

`resend_keyed_orders=True` makes the SDK do option 1 itself, once: an order with a key that hits a timeout or a 5xx on the first attempt is sent again with the same key. A second failure raises `OutcomeUnknownError` as usual.

```python
fc = FazerCards(resend_keyed_orders=True)
```

It is off by default because it relies on FazerCards honouring the key. Turn it on when you pass your own keys.

## Telegram purchases

The API takes no key on Telegram Stars and Premium. Those calls are never resent, not even with `resend_keyed_orders`. See [Telegram](telegram.md#no-idempotency-key).
