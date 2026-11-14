# Async

`AsyncFazerCards` has the same namespaces, methods and results as `FazerCards`. Add `await`.

```python
import asyncio

from fazercards_sdk import AsyncFazerCards


async def main() -> None:
    async with AsyncFazerCards() as fc:
        balance, games, cards = await asyncio.gather(
            fc.balance(),
            fc.topups.all_categories(),
            fc.giftcards.all_categories(),
        )
        print(balance.amount, len(games), len(cards))


asyncio.run(main())
```

## Notes

- Use `async with` or `await fc.close()`. `http_client=` must be an `httpx.AsyncClient`.
- `verify_webhook` is a plain method on the async client too; it makes no request, so there is nothing to await.
- `fc.rate_limit` is a plain attribute.
- Backoff waits, the waits between gift card code reads and `orders.wait` all use `asyncio.sleep`.
- One client can serve a whole web application. Create it at start up and close it at shut down.

## In FastAPI

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fazercards_sdk import AsyncFazerCards

fazercards = AsyncFazerCards()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await fazercards.close()


app = FastAPI(lifespan=lifespan)


@app.get("/games")
async def games():
    return [{"id": c.category_id, "name": c.name} for c in await fazercards.topups.all_categories()]
```

## Parallel orders

Orders for different customers can run side by side; each has its own key. Keep the number of parallel requests reasonable and watch `fc.rate_limit.remaining`.
