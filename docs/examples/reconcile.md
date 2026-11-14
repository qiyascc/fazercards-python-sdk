# Reconcile unknown orders

When an order call times out, the shop does not know whether FazerCards placed it. The [idempotency guide](../guides/idempotency.md) recommends marking such orders and settling them later. This job does the settling: for each unknown order it sends the same order again with the same key, which returns the existing order if there is one and places it otherwise.

The example keeps its state in a JSON file; in a real shop it is a table.

```python
import json
import sys
from pathlib import Path

from fazercards_sdk import FazerCards, FazerCardsError, KeyCollisionError, OutcomeUnknownError

STATE = Path("unknown-orders.json")


def settle(fc: FazerCards, item: dict) -> dict:
    if item["kind"] == "giftcard":
        order = fc.giftcards.order(item["category_id"], item["offer_id"], item.get("quantity", 1),
                                   idempotency_key=item["key"])
    elif item["kind"] == "topup":
        order = fc.topups.order(item["category_id"], item["offer_id"], fields=item["fields"],
                                idempotency_key=item["key"])
    else:
        raise ValueError(f"cannot settle {item['kind']} automatically")
    return {**item, "state": "settled", "order_id": order.id, "status": str(order.status)}


def main() -> int:
    items = json.loads(STATE.read_text()) if STATE.exists() else []
    left = 0
    with FazerCards() as fc:
        for index, item in enumerate(items):
            if item.get("state") != "unknown":
                continue
            try:
                items[index] = settle(fc, item)
                print("settled", item["key"], items[index]["order_id"], items[index]["status"])
            except OutcomeUnknownError:
                left += 1
                print("still no answer for", item["key"])
            except KeyCollisionError as exc:
                items[index] = {**item, "state": "collision", "note": str(exc)}
                print("key collision", item["key"])
            except (FazerCardsError, ValueError) as exc:
                left += 1
                print("could not settle", item["key"], exc)
    STATE.write_text(json.dumps(items, indent=2))
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
```

`unknown-orders.json` holds what the shop tried to buy:

```json
[
  {"state": "unknown", "kind": "giftcard", "key": "purchase-1043",
   "category_id": "playstation_tr", "offer_id": "250_try", "quantity": 1},
  {"state": "unknown", "kind": "topup", "key": "purchase-1044",
   "category_id": "free_fire_cis", "offer_id": "110_diamonds", "fields": {"player_id": "123456789"}}
]
```

Why this is safe:

- The key is the shop's own purchase id, the same key the first attempt used. FazerCards hands back the first order if it exists, so nothing is bought twice.
- A `KeyCollisionError` means the key belongs to an order for another item. That needs a person; the job marks it and moves on.
- Run the job with the same `idempotency_prefix` as the shop (the environment variable does that), or the keys will not match.
- Telegram purchases have no key, so they are not settled automatically. Look them up in `fc.orders.recent()` by hand.
