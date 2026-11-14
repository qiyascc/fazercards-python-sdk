# Errors

Every exception inherits from {py:class}`~fazercards_sdk.FazerCardsError`.

## The hierarchy

```text
FazerCardsError
├── ConfigurationError        no API key, no webhook secret, plain http
├── InvalidRequestError       a bad argument, found before sending (also a ValueError)
├── SignatureError            a webhook that fails the signature or payload checks
├── KeyCollisionError         a reused Idempotency-Key returned an order for another item
├── WaitTimeoutError          orders.wait ran out of time
├── TransportError            no usable answer
│   ├── NotSentError          the connection failed, nothing was sent
│   └── OutcomeUnknownError   an order may or may not have been placed
└── APIError                  FazerCards answered with an error, or with "ok": false
    ├── BadRequestError       400 and other 4xx
    ├── AuthenticationError   401 or 403: a wrong or disabled API key
    ├── NotFoundError         404
    ├── ConflictError         409
    ├── RateLimitError        429 after the retries
    └── ServerError           5xx after the retries
```

## Attributes

| Exception | Attributes |
| --- | --- |
| all | `message` |
| `TransportError` and below | `path`, `idempotency_key` (the key of the order, when there was one) |
| `OutcomeUnknownError` | `status_code` when there was an answer |
| `APIError` and below | `status_code`, `body`, `path` |
| `RateLimitError` | `retry_after` |
| `KeyCollisionError` | `idempotency_key`, `order` (the answer FazerCards gave) |
| `WaitTimeoutError` | `order`: the last read |

`str()` of an `APIError` starts with the status code in brackets. The message is FazerCards' own `message` or `error` field when it sent one.

An answer with `"ok": false` and status 200 is a refusal too; it raises a plain `APIError`.

## Which one to catch

| You want to | Catch |
| --- | --- |
| Tell the customer the input is wrong | `InvalidRequestError`, `BadRequestError` |
| Fix the setup | `ConfigurationError`, `AuthenticationError` |
| Look the order up, or resend with the same key | `OutcomeUnknownError` |
| Stop and investigate | `KeyCollisionError` |
| Try again later | `RateLimitError`, `ServerError`, `NotSentError`, `TransportError` |
| Reject a webhook | `SignatureError` |

```python
from fazercards_sdk import (
    BadRequestError,
    FazerCardsError,
    InvalidRequestError,
    KeyCollisionError,
    OutcomeUnknownError,
)

try:
    order = fc.topups.order(category, offer, player_id, idempotency_key=shop_order)
except (InvalidRequestError, BadRequestError) as exc:
    tell_customer(str(exc))
except OutcomeUnknownError as exc:
    queue_for_lookup(shop_order, exc.idempotency_key)
except KeyCollisionError as exc:
    alert_admin(f"key {exc.idempotency_key} reused for another item")
except FazerCardsError as exc:
    retry_later(shop_order, exc)
```

## Messages

Every message comes from `messages.yaml` and can be replaced; see [Messages](messages.md).
