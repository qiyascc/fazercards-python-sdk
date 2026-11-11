from fastapi import FastAPI, HTTPException, Request

from fazercards_sdk import AsyncFazerCards, SignatureError

app = FastAPI()
fazercards = AsyncFazerCards()


@app.post("/webhook/fazercards")
async def fazercards_webhook(request: Request) -> dict:
    try:
        event = fazercards.verify_webhook(await request.body(), headers=request.headers)
    except SignatureError:
        raise HTTPException(status_code=401) from None
    order = await fazercards.orders.get(event.order_id) if event.needs_lookup else event.order
    if order is None:
        return {"message": "OK"}
    if order.delivered and not order.awaiting_codes:
        await deliver(order.id, order.codes)
    elif order.failed:
        await refund(order.id, order.fail_reason)
    return {"message": "OK"}


async def deliver(order_id: str, codes: tuple[str, ...]) -> None:
    raise NotImplementedError


async def refund(order_id: str, reason: str | None) -> None:
    raise NotImplementedError
