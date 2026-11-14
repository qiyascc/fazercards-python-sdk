# Catalog

FazerCards sells two kinds of catalog items: **top-ups**, which are credited to a player account in a game, and **gift cards**, which are codes. Both are organised the same way: categories (a game or a card brand in a region) that hold offers (the packages you can buy).

| | Top-ups | Gift cards |
| --- | --- | --- |
| Categories | `fc.topups.categories()`, `all_categories()` | `fc.giftcards.categories()`, `all_categories()` |
| Offers | `fc.topups.offers(category_id)` | `fc.giftcards.offers(category_id)` or `cards(category_id)` |
| Order | [Top-ups](topups.md) | [Gift cards](giftcards.md) |

All catalog calls are reads and are retried on network trouble.

## Categories

```python
page = fc.topups.categories(limit=100)
for category in page.items:
    print(category.category_id, category.name, category.note)
if page.has_more:
    page = fc.topups.categories(limit=100, cursor=page.next_cursor)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `limit` | `100` | Page size, 1 to 500 |
| `cursor` | `None` | `next_cursor` of the previous page |
| `include_ui` | `True` | Ask FazerCards to include display data such as images |

{py:class}`~fazercards_sdk.CategoryPage` has `items`, `total`, `limit`, `next_cursor` and `has_more`.

Every category at once, following the cursor with pages of 500:

```python
games = fc.topups.all_categories()
cards = fc.giftcards.all_categories()
```

`all_categories(include_ui=True, max_pages=50)` returns a tuple of {py:class}`~fazercards_sdk.Category`:

| Field | Meaning |
| --- | --- |
| `category_id` | The id used everywhere else, such as `free_fire_cis` or `playstation_tr` |
| `name` | The display name |
| `note` | A note from FazerCards about the category |
| `image_url` | An image, when `include_ui` is on |
| `kind` | The kind FazerCards reports for the page |
| `raw` | The whole item |

## Offers

```python
offers = fc.topups.offers("free_fire_cis")
print(offers.name, offers.note)
for offer in offers.offers:
    print(offer.id, offer.name, offer.price, offer.stock, offer.in_stock)
```

{py:class}`~fazercards_sdk.Offers` describes one category:

| Field | Meaning |
| --- | --- |
| `category_id`, `name`, `kind`, `note`, `image_url` | The category |
| `offers` | A tuple of `Offer` |
| `fields` | A tuple of `InputField`: what an order in this category needs |
| `get(offer_id)` | The `Offer` with that id, or `None` |

Each {py:class}`~fazercards_sdk.Offer`:

| Field | Meaning |
| --- | --- |
| `id` | The offer id (`offer_id` for top-ups, `card_id` for gift cards) |
| `name` | Display name, such as `110 Diamonds` or `250 TRY` |
| `price` | Price in USD as a `Decimal` |
| `stock` | Units in stock, when FazerCards says. `None` means not reported |
| `in_stock` | `True` when `stock` is `None` or above 0 |
| `min_quantity`, `max_quantity` | Order limits per order, when given |

## Input fields

`offers.fields` lists what an order needs, as {py:class}`~fazercards_sdk.InputField` objects:

| Field | Meaning |
| --- | --- |
| `key` | The name to use in the order, such as `player_id` or `server_id` |
| `label` | What to show your customer |
| `type` | The input type, `text` by default |
| `required` | Whether the order needs it |
| `options` | For fields with fixed choices, the choices |

Build your checkout form from these, so a new game with an extra field works without code changes:

```python
offers = fc.topups.offers(category_id)
form = {field.key: input(f"{field.label or field.key}: ") for field in offers.fields if field.required}
order = fc.topups.order(category_id, offer_id, fields=form, idempotency_key=shop_order)
```

## Caching

Catalogs change during the day, prices and stock more often. Cache the category list for hours if you like, but read `offers()` close to the moment of sale so the price your customer sees is current.
