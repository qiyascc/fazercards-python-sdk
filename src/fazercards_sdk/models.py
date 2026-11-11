from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Optional

from .enums import OrderKind, OrderStatus
from .money import parse


def _pick(body: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = body.get(key)
        if value is not None and value != "":
            return value
    return None


def _str(body: Mapping[str, Any], *keys: str) -> Optional[str]:
    value = _pick(body, *keys)
    return None if value is None else str(value)


def _int(body: Mapping[str, Any], *keys: str) -> Optional[int]:
    value = _pick(body, *keys)
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool(body: Mapping[str, Any], *keys: str) -> Optional[bool]:
    value = _pick(body, *keys)
    return value if isinstance(value, bool) else None


def _money(body: Mapping[str, Any], *keys: str) -> Optional[Decimal]:
    return parse(_pick(body, *keys))


def _when(body: Mapping[str, Any], *keys: str) -> Optional[datetime]:
    value = _pick(body, *keys)
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def card_code(card: Any) -> str:
    if isinstance(card, Mapping):
        parts = [str(card[key]) for key in ("code", "serial", "pin") if card.get(key) not in (None, "")]
        return " / ".join(parts) if parts else str(dict(card))
    return str(card)


@dataclass(frozen=True)
class Balance:
    amount: Decimal
    currency: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Balance:
        return cls(_money(body, "balance") or Decimal("0"), _str(body, "currency") or "USD", dict(body))


@dataclass(frozen=True)
class Account:
    login: Optional[str]
    email: Optional[str]
    plan: Optional[str]
    plan_expires_at: Optional[datetime]
    plan_auto_renew: Optional[bool]
    subscription_active: Optional[bool]
    total_spent: Optional[Decimal]
    total_orders: Optional[int]
    created_at: Optional[datetime]
    last_active_at: Optional[datetime]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Account:
        summary = _map(body.get("summary"))
        return cls(
            login=_str(body, "login"),
            email=_str(body, "email"),
            plan=_str(body, "plan"),
            plan_expires_at=_when(body, "planExpiresAt", "plan_expires_at"),
            plan_auto_renew=_bool(body, "planAutoRenew", "plan_auto_renew"),
            subscription_active=_bool(body, "subscriptionActive", "subscription_active"),
            total_spent=_money(summary, "totalSpent", "total_spent"),
            total_orders=_int(summary, "totalOrders", "total_orders"),
            created_at=_when(body, "createdAt", "created_at"),
            last_active_at=_when(body, "lastActiveAt", "last_active_at"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class InputField:
    key: str
    label: Optional[str] = None
    type: str = "text"
    required: bool = True
    options: tuple[Any, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> InputField:
        required = body.get("required")
        return cls(
            key=_str(body, "key", "name") or "",
            label=_str(body, "label"),
            type=_str(body, "type") or "text",
            required=required if isinstance(required, bool) else True,
            options=tuple(_list(body.get("options"))),
            raw=dict(body),
        )


@dataclass(frozen=True)
class Category:
    category_id: str
    name: str
    note: Optional[str] = None
    image_url: Optional[str] = None
    kind: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any], kind: Optional[str] = None) -> Category:
        return cls(
            category_id=_str(body, "category_id", "id") or "",
            name=_str(body, "name") or "",
            note=_str(body, "note"),
            image_url=_str(body, "imageurl", "image_url", "image"),
            kind=kind,
            raw=dict(body),
        )


@dataclass(frozen=True)
class CategoryPage:
    items: tuple[Category, ...]
    total: Optional[int]
    limit: Optional[int]
    next_cursor: Optional[str]
    has_more: bool

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> CategoryPage:
        meta = _map(body.get("meta"))
        kind = _str(body, "kind")
        cursor = _str(meta, "next_cursor")
        return cls(
            items=tuple(Category.from_api(i, kind) for i in _list(body.get("items")) if isinstance(i, Mapping)),
            total=_int(meta, "total"),
            limit=_int(meta, "limit"),
            next_cursor=cursor,
            has_more=bool(meta.get("has_more")) and cursor is not None,
        )


@dataclass(frozen=True)
class Offer:
    id: str
    name: str
    price: Optional[Decimal]
    stock: Optional[int] = None
    min_quantity: int = 1
    max_quantity: Optional[int] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def in_stock(self) -> bool:
        return self.stock is None or self.stock > 0

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Offer:
        return cls(
            id=_str(body, "offer_id", "card_id", "id") or "",
            name=_str(body, "name") or "",
            price=_money(body, "price_usd", "price"),
            stock=_int(body, "stock"),
            min_quantity=_int(body, "min_order_quantity", "min_quantity") or 1,
            max_quantity=_int(body, "max_order_quantity", "max_quantity"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class Offers:
    category_id: str
    name: str
    kind: Optional[str]
    offers: tuple[Offer, ...]
    fields: tuple[InputField, ...] = ()
    note: Optional[str] = None
    image_url: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def get(self, offer_id: str) -> Optional[Offer]:
        return next((offer for offer in self.offers if offer.id == offer_id), None)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Offers:
        return cls(
            category_id=_str(body, "category_id") or "",
            name=_str(body, "name") or "",
            kind=_str(body, "kind"),
            offers=tuple(Offer.from_api(item) for item in _list(body.get("offers")) if isinstance(item, Mapping)),
            fields=tuple(InputField.from_api(item) for item in _list(body.get("fields")) if isinstance(item, Mapping)),
            note=_str(body, "note"),
            image_url=_str(body, "imageurl", "image_url", "image"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class ValidationGame:
    category_id: str
    name: str
    fields: tuple[InputField, ...]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> ValidationGame:
        return cls(
            category_id=_str(body, "category_id") or "",
            name=_str(body, "name") or "",
            fields=tuple(InputField.from_api(item) for item in _list(body.get("fields")) if isinstance(item, Mapping)),
            raw=dict(body),
        )


@dataclass(frozen=True)
class PlayerCheck:
    valid: Optional[bool]
    category_id: Optional[str] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    region: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> PlayerCheck:
        return cls(
            valid=_bool(body, "valid"),
            category_id=_str(body, "category_id"),
            player_id=_str(body, "player_id"),
            player_name=_str(body, "player_name"),
            region=_str(body, "region"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class SteamLogin:
    can_refill: Optional[bool]
    unverified: bool = False
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def valid(self) -> Optional[bool]:
        if self.can_refill:
            return True
        return None if self.unverified or self.can_refill is None else False

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> SteamLogin:
        return cls(_bool(body, "can_refill", "canRefill"), bool(_bool(body, "unverified")), dict(body))


@dataclass(frozen=True)
class SteamRates:
    base: str
    rates: Mapping[str, Decimal]
    updated_at: Optional[datetime] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def convert(self, usd: Decimal, currency: str) -> Optional[Decimal]:
        rate = self.rates.get(str(currency).upper())
        return None if rate is None else usd * rate

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> SteamRates:
        rates = {str(code).upper(): value for code, raw in _map(body.get("rates")).items()
                 if (value := parse(raw)) is not None}
        return cls(_str(body, "base") or "USD", rates, _when(body, "updated_at", "updatedAt"), dict(body))


@dataclass(frozen=True)
class StarsQuote:
    price_per_star: Decimal
    min_amount: int
    max_amount: int
    rates_updated_at: Optional[datetime] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def price(self, quantity: int) -> Decimal:
        return self.price_per_star * quantity

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> StarsQuote:
        return cls(
            price_per_star=_money(body, "price_per_star") or Decimal("0"),
            min_amount=_int(body, "min_amount") or 50,
            max_amount=_int(body, "max_amount") or 100000,
            rates_updated_at=_when(body, "rates_updated_at"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class PremiumPlan:
    months: int
    price: Decimal


@dataclass(frozen=True)
class PremiumQuote:
    plans: tuple[PremiumPlan, ...]
    rates_updated_at: Optional[datetime] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def plan(self, months: int) -> Optional[PremiumPlan]:
        return next((plan for plan in self.plans if plan.months == months), None)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> PremiumQuote:
        plans = []
        for item in _list(body.get("plans")):
            if not isinstance(item, Mapping):
                continue
            months, price = _int(item, "months"), _money(item, "price_usd", "price")
            if months is not None and price is not None:
                plans.append(PremiumPlan(months, price))
        return cls(tuple(plans), _when(body, "rates_updated_at"), dict(body))


@dataclass(frozen=True)
class StatusChange:
    status: OrderStatus
    at: Optional[datetime]


@dataclass(frozen=True)
class Order:
    id: str
    kind: OrderKind
    status: OrderStatus
    title: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    offer_id: Optional[str] = None
    offer_name: Optional[str] = None
    quantity: Optional[int] = None
    fields: Mapping[str, Any] = field(default_factory=dict)
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None
    codes: tuple[str, ...] = ()
    fail_reason: Optional[str] = None
    history: tuple[StatusChange, ...] = ()
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def delivered(self) -> bool:
        return self.status.delivered

    @property
    def failed(self) -> bool:
        return self.status.failed

    @property
    def in_flight(self) -> bool:
        return self.status.in_flight

    @property
    def awaiting_codes(self) -> bool:
        return self.kind is OrderKind.GIFT_CARD and self.delivered and not self.codes

    def with_key(self, key: Optional[str]) -> Order:
        return replace(self, idempotency_key=key)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Order:
        order = _map(body.get("order")) or body
        history = tuple(
            StatusChange(OrderStatus.of(item.get("status")), _when(item, "at"))
            for item in _list(_pick(order, "status_history", "statusHistory"))
            if isinstance(item, Mapping)
        )
        return cls(
            id=_str(order, "id", "order_id") or "",
            kind=OrderKind.of(order.get("kind")),
            status=OrderStatus.of(order.get("status")),
            title=_str(order, "title"),
            category_id=_str(order, "category_id"),
            category_name=_str(order, "category_name"),
            offer_id=_str(order, "offer_id", "card_id"),
            offer_name=_str(order, "offer_name"),
            quantity=_int(order, "quantity", "stars_quantity", "starsQuantity", "months"),
            fields=dict(_map(order.get("fields"))),
            unit_price=_money(order, "price_usd_per_unit", "price_usd"),
            total=_money(order, "total_usd", "chargedUsd", "charged_usd", "amountUsd"),
            codes=tuple(card_code(card) for card in _list(order.get("cards")) if card not in (None, "")),
            fail_reason=_str(order, "fail_reason", "failReason"),
            history=history,
            created_at=_when(order, "created_at", "createdAt"),
            completed_at=_when(order, "completed_at", "completedAt"),
            raw=dict(order),
        )


@dataclass(frozen=True)
class OrderPage:
    items: tuple[Order, ...]
    total: Optional[int]
    page: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.total is not None and self.page * self.limit < self.total

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> OrderPage:
        return cls(
            items=tuple(Order.from_api(item) for item in _list(body.get("items")) if isinstance(item, Mapping)),
            total=_int(body, "total"),
            page=_int(body, "page") or 1,
            limit=_int(body, "limit") or 20,
        )


@dataclass(frozen=True)
class Webhook:
    url: Optional[str]
    enabled: bool
    consecutive_failures: int = 0
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> Webhook:
        hook = _map(body.get("webhook")) or body
        return cls(
            url=_str(hook, "url"),
            enabled=bool(_bool(hook, "enabled")),
            consecutive_failures=_int(hook, "consecutive_failures") or 0,
            last_success_at=_when(hook, "last_success_at"),
            last_failure_at=_when(hook, "last_failure_at"),
            last_failure_reason=_str(hook, "last_failure_reason"),
            created_at=_when(hook, "created_at"),
            updated_at=_when(hook, "updated_at"),
            raw=dict(hook),
        )


@dataclass(frozen=True)
class WebhookEvent:
    order_id: Optional[str]
    status: OrderStatus
    order: Optional[Order]
    merchant_txn_id: Optional[str] = None
    event: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def needs_lookup(self) -> bool:
        return self.order_id is not None and (self.status is OrderStatus.UNKNOWN or self.order is None)

    @classmethod
    def from_api(cls, body: Mapping[str, Any]) -> WebhookEvent:
        order = _map(body.get("order")) or _map(body.get("data")) or body
        if isinstance(order.get("order"), Mapping):
            order = order["order"]
        order_id = _str(order, "id", "order_id") or _str(body, "order_id", "id")
        status = OrderStatus.of(_pick(order, "status") or body.get("status"))
        parsed = Order.from_api(order) if _str(order, "id", "order_id") and _pick(order, "status") else None
        return cls(
            order_id=order_id,
            status=status,
            order=parsed,
            merchant_txn_id=_str(order, "merchant_txn_id") or _str(body, "merchant_txn_id"),
            event=_str(body, "event", "type"),
            raw=dict(body),
        )


@dataclass(frozen=True)
class RateLimit:
    limit: Optional[int]
    remaining: Optional[int]
    reset: Optional[float]
