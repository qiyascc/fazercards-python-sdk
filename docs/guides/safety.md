# Safety and retries

Reads can be repeated freely. Orders cannot: a repeated order spends your balance twice. The SDK treats them differently.

## Reads and orders

| Kind | Calls | On a timeout, a cut connection or a 5xx |
| --- | --- | --- |
| Reads | `balance`, `account.*`, every catalog call, `topups.validate`, `steam.check_login`, `steam.rates`, `telegram.*_quote`, `orders.*`, the code reads after a gift card order | Retried with backoff, then `TransportError` or `ServerError` |
| Keyed orders | `topups.order`, `giftcards.order`, `steam.order` | Not retried, `OutcomeUnknownError` with the key. With `resend_keyed_orders=True`, resent once with the same key |
| Telegram purchases | `telegram.buy_stars`, `telegram.buy_premium` | Never retried, `OutcomeUnknownError` |

`account.set_webhook` only stores an address and is retried like a read. `fc.request(...)` treats `GET` as a read and other methods as orders unless you pass `safe=`.

## Every situation

| Situation | What the client does |
| --- | --- |
| Connection refused, nothing sent | Retries, then `NotSentError` |
| Timeout, cut connection or 5xx on an order | No retry, `OutcomeUnknownError` with the `idempotency_key` |
| Same failure on a read | Retries with backoff, then `TransportError` |
| An order answered with something that is not JSON | `OutcomeUnknownError` |
| 429 | Waits for `Retry-After` or `X-RateLimit-Reset` (at most `backoff_cap`) and retries; the request was not processed |
| `resend_keyed_orders=True` | An order with an Idempotency-Key is resent once with the same key |
| Telegram purchase | Takes no key on the API side, so it is never resent |
| Reused key that returns another item | `KeyCollisionError`, never counted as success |
| Gift card `completed` without codes | Read again, then `order.awaiting_codes` |
| Quantity, months, amount like `1.005` or `True` | `InvalidRequestError` before anything is sent |
| `base_url` over plain http | `ConfigurationError`, except localhost or `allow_insecure_http` |
| Webhook body over 256 KB | Rejected before hashing |

## Backoff

The wait before retry `n` (from 0) is `min(backoff_cap, backoff_base * 2 ** n)` plus a random part up to `backoff_base / 2`. With the defaults (`max_retries=2`, `backoff_base=0.5`, `backoff_cap=8`) a read is tried three times, waiting about 0.5 and 1 second.

## After an unknown outcome

| Order | What to do |
| --- | --- |
| Top-up, gift card, Steam | Send it again with the same `idempotency_key`; FazerCards returns the first order if it exists. Or look it up in `orders.recent()` |
| Telegram | Look it up in `orders.recent()` before buying again; there is no key to protect a resend |

Mark the order in your own database before calling FazerCards, and only mark it done after you have the FazerCards order id. Then a crash at any point leaves a record that tells you what to check.

## The API key

The key is sent to `base_url` only, over https. A plain http address other than localhost is refused when the client is created.
