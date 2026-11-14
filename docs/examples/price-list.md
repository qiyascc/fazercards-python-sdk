# Price list

Every offer of every top-up and gift card category, with your selling price, written to a CSV file. Useful for updating a shop's catalog or for checking prices by hand.

```python
import csv
import sys
from decimal import ROUND_HALF_UP, Decimal

from fazercards_sdk import FazerCards, FazerCardsError

MARGIN = Decimal("1.10")
CENT = Decimal("0.01")
FIELDS = ["kind", "category_id", "category", "offer_id", "offer", "cost_usd", "price_usd", "stock", "needs"]


def rows(fc: FazerCards):
    for kind, resource in (("topup", fc.topups), ("gift_card", fc.giftcards)):
        for category in resource.all_categories(include_ui=False):
            try:
                offers = resource.offers(category.category_id, include_ui=False)
            except FazerCardsError as exc:
                print(f"skipped {category.category_id}: {exc}", file=sys.stderr)
                continue
            needs = " ".join(field.key for field in offers.fields if field.required)
            for offer in offers.offers:
                if offer.price is None or not offer.in_stock:
                    continue
                yield {
                    "kind": kind,
                    "category_id": category.category_id,
                    "category": category.name,
                    "offer_id": offer.id,
                    "offer": offer.name,
                    "cost_usd": offer.price,
                    "price_usd": (offer.price * MARGIN).quantize(CENT, rounding=ROUND_HALF_UP),
                    "stock": "" if offer.stock is None else offer.stock,
                    "needs": needs,
                }


def main(path: str) -> None:
    with FazerCards() as fc, open(path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        count = 0
        for row in rows(fc):
            writer.writerow(row)
            count += 1
    print(f"{count} offers written to {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fazercards-prices.csv")
```

- `include_ui=False` leaves out images and display data, which keeps the answers small.
- Out of stock offers and offers without a price are skipped.
- A category that fails to load is reported and skipped, so one bad category does not stop the whole list.
- Prices stay `Decimal` from FazerCards to the file; the csv module writes them as plain text such as `5.35`.
- The `needs` column lists the fields a top-up order requires, such as `player_id server_id`.

The script makes one request per category, so a full run takes a while. Run it every few hours, not on every page view.
