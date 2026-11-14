# Advanced use

## Any API call

`fc.request` sends any call under `base_url` with the same key, headers, retries and errors as the built in methods:

```python
data = fc.request("GET", "/balance")
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `method` | | `GET`, `POST`, `PUT`, ... |
| `path` | | A path under `base_url`. A missing leading `/` is added |
| `body` | `None` | Sent as JSON for methods other than `GET` |
| `safe` | `GET` only | Whether the call may be retried |
| `idempotency_key` | `None` | Sent as `Idempotency-Key` as given, without the prefix |

It returns the parsed JSON answer as it came.

## The client object

`repr(fc)` shows the base address only. `fc.settings` is the loaded {py:class}`~fazercards_sdk.Settings`; `fc.settings.scoped("1042")` shows how a key looks with the configured prefix. Create a new client to change settings.

## Your own httpx client

```python
import logging

import httpx

from fazercards_sdk import FazerCards

log = logging.getLogger("fazercards")


def show(response: httpx.Response) -> None:
    log.info("%s %s -> %s", response.request.method, response.request.url.path, response.status_code)


fc = FazerCards(http_client=httpx.Client(timeout=30, event_hooks={"response": [show]}))
```

Never log headers: `X-API-Key` is one of them.

## Two shops, one process

Give each shop its own client with its own prefix:

```python
shops = {
    "a": FazerCards(idempotency_prefix="shop-a"),
    "b": FazerCards(idempotency_prefix="shop-b"),
}
```

## Threads

A sync client can be shared between threads. It holds no per call state except `rate_limit`, which simply shows the last answer's headers.
