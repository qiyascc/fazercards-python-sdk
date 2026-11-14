# Django checkout

A Django shop that sells gift cards: the order model, a fulfilment function that uses the shop's order id as the idempotency key, and a webhook view.

## Settings

```python
FAZERCARDS_API_KEY = env("FAZERCARDS_API_KEY")
FAZERCARDS_WEBHOOK_SECRET = env("FAZERCARDS_WEBHOOK_SECRET")
```

## Model

```python
from django.db import models


class Purchase(models.Model):
    class State(models.TextChoices):
        PAID = "paid"
        PLACING = "placing"
        UNKNOWN = "unknown"
        WAITING = "waiting"
        DELIVERED = "delivered"
        FAILED = "failed"

    category_id = models.CharField(max_length=100)
    card_id = models.CharField(max_length=100)
    quantity = models.PositiveSmallIntegerField(default=1)
    state = models.CharField(max_length=10, choices=State.choices, default=State.PAID)
    fazercards_id = models.CharField(max_length=64, blank=True, db_index=True)
    codes = models.JSONField(default=list, blank=True)
    note = models.TextField(blank=True)

    @property
    def key(self) -> str:
        return f"purchase-{self.pk}"
```

## Client

```python
from functools import cache

from django.conf import settings

from fazercards_sdk import FazerCards


@cache
def fazercards() -> FazerCards:
    return FazerCards(settings.FAZERCARDS_API_KEY, webhook_secret=settings.FAZERCARDS_WEBHOOK_SECRET,
                      resend_keyed_orders=True)
```

`resend_keyed_orders=True` is safe here because every order carries the purchase's own key.

## Fulfilment

```python
from fazercards_sdk import FazerCardsError, KeyCollisionError, Order, OutcomeUnknownError

from .client import fazercards
from .models import Purchase


def apply(purchase: Purchase, order: Order) -> None:
    purchase.fazercards_id = order.id
    if order.awaiting_codes or order.in_flight:
        purchase.state = Purchase.State.WAITING
    elif order.delivered:
        purchase.state, purchase.codes = Purchase.State.DELIVERED, list(order.codes)
    elif order.failed:
        purchase.state, purchase.note = Purchase.State.FAILED, order.fail_reason or ""
    purchase.save()


def fulfil(purchase: Purchase) -> None:
    purchase.state = Purchase.State.PLACING
    purchase.save(update_fields=["state"])
    try:
        order = fazercards().giftcards.order(purchase.category_id, purchase.card_id, purchase.quantity,
                                             idempotency_key=purchase.key)
    except OutcomeUnknownError as exc:
        purchase.state, purchase.note = Purchase.State.UNKNOWN, str(exc)
        purchase.save()
        return
    except KeyCollisionError as exc:
        purchase.state, purchase.note = Purchase.State.FAILED, str(exc)
        purchase.save()
        return
    except FazerCardsError as exc:
        purchase.state, purchase.note = Purchase.State.PAID, str(exc)
        purchase.save()
        return
    apply(purchase, order)
```

Call `fulfil` from a background task after the customer has paid. Because the key is the purchase id, calling it again for the same purchase, after a crash or for an `UNKNOWN` row, never buys a second card.

## Webhook view

```python
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from fazercards_sdk import SignatureError

from .client import fazercards
from .fulfil import apply
from .models import Purchase


@csrf_exempt
@require_POST
def fazercards_webhook(request):
    try:
        event = fazercards().verify_webhook(request.body, headers=request.headers)
    except SignatureError:
        return HttpResponse(status=401)
    order = fazercards().orders.get(event.order_id) if event.needs_lookup else event.order
    if order is not None:
        purchase = Purchase.objects.filter(fazercards_id=order.id).first()
        if purchase and purchase.state not in (Purchase.State.DELIVERED, Purchase.State.FAILED):
            apply(purchase, order)
    return JsonResponse({"message": "OK"})
```

`request.body` is the raw body Django received, which is what the signature check needs. `request.headers` is case insensitive, and so is the SDK's header lookup.
