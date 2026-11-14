# Gift cards

A gift card order buys one or more codes for a brand in a region, such as PlayStation Turkey 250 TRY. The codes come back on the order.

## Find the card

```python
cards = fc.giftcards.cards("playstation_tr")
for card in cards.offers:
    print(card.id, card.name, card.price, card.stock)
```

`cards(category_id)` is the same as `offers(category_id)`; see [Catalog](catalog.md#offers). Check `card.in_stock` before selling.

## Order

```python
order = fc.giftcards.order("playstation_tr", "250_try", quantity=1, idempotency_key="ORDER-1043")
for code in order.codes:
    print(code)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `category_id` | | The gift card category |
| `card_id` | | The card, from `cards()` |
| `quantity` | `1` | 1 to 100 codes |
| `idempotency_key` | random | Your order number. Strongly recommended |
| `wait_for_codes` | `True` | Read the order again when it is completed without codes |

`order.codes` is a tuple of strings. When FazerCards sends a card as an object with a code, a serial and a PIN, they are joined as `code / serial / pin`. The original card objects are in `order.raw["cards"]`.

## Codes that arrive late

FazerCards can answer a gift card order with `completed` and an empty card list, and fill the list a moment later. The SDK handles this:

1. When the order comes back completed without codes, it reads the order again at once.
2. If the codes are still missing it waits `code_check_wait` seconds (1 by default) and reads again.
3. It stops after `code_checks` reads (3 by default) or as soon as the codes are there.

If the codes still have not arrived, `order.awaiting_codes` is `True`. Keep the order open and read it later, from a webhook or with `fc.orders.get(order.id)`. Never show your customer an empty result as if the purchase were finished.

```python
order = fc.giftcards.order("playstation_tr", "250_try", idempotency_key=shop_order)
if order.awaiting_codes:
    mark_as_waiting(shop_order, order.id)
elif order.delivered:
    send_codes(shop_order, order.codes)
elif order.failed:
    refund(shop_order, order.fail_reason)
```

`awaiting_codes` is `True` only for a gift card order that is delivered and has no codes.

To skip the extra reads, for example inside a request handler that must answer quickly, pass `wait_for_codes=False` or set `code_checks=0`, and pick the codes up from the webhook.

## Safety

- The order is sent once. A timeout or a 5xx raises `OutcomeUnknownError` with the `idempotency_key`; look it up before trying again.
- The extra reads are reads: they are retried on network trouble and never place a second order.
- A reused key that returns another card raises `KeyCollisionError`.
- `quantity` outside 1 to 100, or not a whole number, raises `InvalidRequestError`.
