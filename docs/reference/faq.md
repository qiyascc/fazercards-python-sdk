# FAQ and troubleshooting

## `ConfigurationError: FazerCards api_key is required`

The client found no key in the arguments, the environment (`FAZERCARDS_API_KEY`) or a config file. See [API key](../getting-started/api-key.md).

## `AuthenticationError` on every call

The key is wrong, disabled or missing permissions. Check it in your FazerCards account.

## `OutcomeUnknownError` on an order

The order may have been placed. Send it again with the same `idempotency_key` (it is on the exception), or look it up in `fc.orders.recent()`. Never send it again with a new key. See [Idempotency](../guides/idempotency.md#unknown-outcomes).

## `KeyCollisionError`

You reused a key that already belongs to an order for another item. Each purchase needs its own key. Look at `exc.order` to see which order holds the key.

## A gift card order is completed but `codes` is empty

FazerCards sometimes attaches the codes a moment after completing the order. The SDK reads the order again up to `code_checks` times; if the codes are still missing, `order.awaiting_codes` is `True`. Read the order again later, or wait for the webhook. See [Gift cards](../guides/giftcards.md#codes-that-arrive-late).

## `SignatureError` on every webhook

- The secret on the client must be the webhook secret, not the API key.
- Pass the raw request body. A body parsed and dumped again does not match.
- Pass the headers or the `X-Webhook-Signature` value.

## `InvalidRequestError: … has more than two decimal places`

Steam amounts take at most two decimals. Round with `Decimal.quantize` before ordering. See [Money](../guides/money.md).

## `username must be a Telegram username of 4 to 32 letters, digits or _`

Telegram usernames are 4 to 32 characters of letters, digits and underscores. A leading `@` is fine; spaces and other characters are not.

## Do I need `resend_keyed_orders`?

Not if you handle `OutcomeUnknownError` yourself. Turn it on when you always pass your own keys and want one automatic resend with the same key after a timeout or a 5xx.

## Why does Telegram never retry?

The API takes no Idempotency-Key for Telegram purchases, so a resend could buy twice. See [Telegram](../guides/telegram.md#no-idempotency-key).

## Prices look like `4.8628`

FazerCards prices top-ups and cards in USD with up to four decimals. They are kept exact as `Decimal`; round them yourself when you show them.
