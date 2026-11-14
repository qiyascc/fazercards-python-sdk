# API key

The FazerCards reseller API identifies your account by an API key. The SDK sends it as the `X-API-Key` header on every request. Get the key from your FazerCards reseller account; this SDK cannot create one.

## Passing the key

The first argument of the client is the key:

```python
from fazercards_sdk import FazerCards

fc = FazerCards("API_KEY")
```

Better, keep it out of the code. The client reads `FAZERCARDS_API_KEY` from the environment:

```bash
export FAZERCARDS_API_KEY=your-api-key
```

Windows CMD:

```bat
set FAZERCARDS_API_KEY=your-api-key
```

```python
fc = FazerCards()
```

It can also come from a config file such as `fazercards.toml`; see [Configuration](configuration.md).

The key is required. A client created without one raises `ConfigurationError` at once, before any request:

```text
ConfigurationError: FazerCards api_key is required
```

## Checking the key

```python
balance = fc.balance()
print(balance.amount, balance.currency)
```

A wrong or disabled key raises `AuthenticationError` (FazerCards answers 401 or 403).

## The webhook secret

Webhooks from FazerCards are signed with a separate secret. Set it as `webhook_secret` (or `FAZERCARDS_WEBHOOK_SECRET`) on the client that receives them; see [Webhooks](../guides/webhooks.md).

## Keeping both safe

- Both settings are pydantic `SecretStr`, so they do not show up when settings are printed.
- `repr(fc)` shows only the base address.
- The client refuses to send the key over plain http to anything but localhost.
- Never log request headers: `X-API-Key` is one of them.
- If a key leaks, replace it in your FazerCards account and update the environment.
