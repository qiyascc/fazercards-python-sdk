# Changelog

## 0.1.1

- `orders.get` leaves the id format to the API and only refuses an empty id or one that would change the path
- Steam amounts always go out with two decimals

## 0.1.0

- Sync `FazerCards` and async `AsyncFazerCards`
- Top-ups, gift cards, Telegram Stars and Premium, Steam wallet, orders, balance, account and webhook settings
- Cursor paged categories and numbered order pages, with helpers that read every page
- Top-up, gift card and Steam orders always carry an Idempotency-Key, with an optional shop prefix
- Orders are never resent after an ambiguous failure; `OutcomeUnknownError` carries the key
- A reused key that returns another item raises `KeyCollisionError`
- Gift card orders that come back completed without codes are read again
- Reads retry with backoff, 429 waits for `Retry-After`, connection failures retry because nothing was sent
- Webhook signature check in constant time, with a body size limit
- goodconf settings, endpoint paths and messages are configurable
