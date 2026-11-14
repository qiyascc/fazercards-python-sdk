# FastAPI webhook

A webhook endpoint that checks the signature, reads the order when the body is not enough, and delivers each order once, even when FazerCards sends the same event several times. SQLite keeps track of what was delivered.

```python
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from fazercards_sdk import AsyncFazerCards, Order, SignatureError

DB = "shop.db"
fazercards = AsyncFazerCards()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.execute("create table if not exists handled (order_id text primary key, outcome text)")
    return conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await fazercards.close()


app = FastAPI(lifespan=lifespan)


def claim(order_id: str, outcome: str) -> bool:
    with db() as conn:
        try:
            conn.execute("insert into handled values (?, ?)", (order_id, outcome))
            return True
        except sqlite3.IntegrityError:
            return False


async def deliver(order: Order) -> None:
    print("deliver", order.id, order.codes)


async def refund(order: Order) -> None:
    print("refund", order.id, order.fail_reason)


@app.post("/webhook/fazercards")
async def fazercards_webhook(request: Request) -> dict:
    try:
        event = fazercards.verify_webhook(await request.body(), headers=request.headers)
    except SignatureError:
        raise HTTPException(status_code=401) from None
    order = await fazercards.orders.get(event.order_id) if event.needs_lookup else event.order
    if order is None or order.in_flight or order.awaiting_codes:
        return {"message": "OK"}
    if order.delivered and claim(order.id, "delivered"):
        await deliver(order)
    elif order.failed and claim(order.id, "failed"):
        await refund(order)
    return {"message": "OK"}
```

Run it with:

```bash
pip install fastapi uvicorn fazercards-python-sdk
export FAZERCARDS_API_KEY=...
export FAZERCARDS_WEBHOOK_SECRET=...
uvicorn webhook:app --port 8000
```

and point FazerCards at it once:

```python
from fazercards_sdk import FazerCards

FazerCards().account.set_webhook("https://shop.example/webhook/fazercards")
```

How it stays correct:

- The signature is checked on the raw body before anything else. A bad one gets 401.
- `claim` inserts the order id into a table with a primary key. Only the first event for an order wins; repeats find the row and do nothing.
- Orders still in flight, and gift cards whose codes have not arrived, are left alone. The next event, or a [reconcile job](reconcile.md), picks them up.
- The endpoint answers quickly with `{"message": "OK"}`. Slow delivery work should go to a queue in a real shop.
