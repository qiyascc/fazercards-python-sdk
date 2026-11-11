from __future__ import annotations

import re
import time
import uuid
from decimal import Decimal
from typing import Any, Mapping, Optional, Union
from urllib.parse import urlsplit

from ._core import Flow, Op, Pause
from .enums import PREMIUM_MONTHS, SteamCurrency
from .errors import InvalidRequestError, WaitTimeoutError
from .messages import text
from .models import (
    Account,
    Balance,
    Category,
    CategoryPage,
    Offers,
    Order,
    OrderPage,
    PlayerCheck,
    PremiumQuote,
    StarsQuote,
    SteamLogin,
    SteamRates,
    ValidationGame,
    Webhook,
)
from .money import Amount, amount, wire

ORDER_ID = re.compile(r"^ord-[0-9]+$")
USERNAME = re.compile(r"^@?([A-Za-z0-9_]{4,32})$")
CATEGORY_PAGE_MAX = 500
ORDER_PAGE_MAX = 100
GIFT_CARD_MAX = 100
STARS_MIN = 50
STARS_MAX = 100000

CurrencyLike = Union[SteamCurrency, str]


def required(value: Any, name: str, limit: int = 255) -> str:
    result = str(value if value is not None else "").strip()
    if not result:
        raise InvalidRequestError(text("value.empty", field=name))
    if len(result) > limit:
        raise InvalidRequestError(text("value.too_long", field=name, limit=limit))
    return result


def whole(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise InvalidRequestError(text("value.range", field=name, low=low, high=high, value=value))
    return value


def order_id(value: Any) -> str:
    result = str(value or "").strip()
    if not ORDER_ID.match(result):
        raise InvalidRequestError(text("value.order_id", value=value))
    return result


def username(value: Any) -> str:
    match = USERNAME.match(str(value or "").strip())
    if not match:
        raise InvalidRequestError(text("value.username", value=value))
    return match.group(1)


def player_fields(fields: Optional[Mapping[str, Any]], **named: Any) -> dict[str, str]:
    if fields is not None and not isinstance(fields, Mapping):
        raise InvalidRequestError(text("value.fields", value=fields))
    merged = {**dict(fields or {}), **{k: v for k, v in named.items() if v is not None}}
    result = {}
    for key, value in merged.items():
        if value is None or isinstance(value, (dict, list, tuple, set)):
            raise InvalidRequestError(text("value.fields", value=fields))
        result[required(key, "field name", 64)] = required(value, str(key), 255)
    if not result:
        raise InvalidRequestError(text("value.empty", field="fields"))
    return result


def https_url(value: Any) -> str:
    result = str(value or "").strip()
    parts = urlsplit(result)
    if parts.scheme != "https" or not parts.hostname:
        raise InvalidRequestError(text("value.url", value=value))
    return result


def _list_of(model: Any, key: str) -> Any:
    return lambda body: tuple(model.from_api(item) for item in (body.get(key) or []) if isinstance(item, Mapping))


class _Resource:
    def __init__(self, client: Any) -> None:
        self._client = client

    @property
    def _settings(self) -> Any:
        return self._client.settings

    def _key(self, given: Optional[str]) -> str:
        return self._settings.scoped(required(given, "idempotency_key", 200) if given else uuid.uuid4().hex)

    def _run(self, op: Op) -> Any:
        return self._client._run(op)

    def _flow(self, flow: Flow[Any]) -> Any:
        return self._client._flow(flow)


class _Catalog(_Resource):
    _categories = ""
    _offers = ""

    def categories(self, limit: int = 100, cursor: Optional[str] = None, include_ui: bool = True) -> Any:
        query = {"limit": whole(limit, "limit", 1, CATEGORY_PAGE_MAX), "cursor": cursor,
                 "include_ui": 1 if include_ui else None}
        return self._run(Op("GET", self._categories, CategoryPage.from_api, query=query, safe=True))

    def all_categories(self, include_ui: bool = True, max_pages: int = 50) -> Any:
        return self._flow(self._every_category(include_ui, max_pages))

    def _every_category(self, include_ui: bool, max_pages: int) -> Flow[tuple[Category, ...]]:
        items: list[Category] = []
        cursor: Optional[str] = None
        for _ in range(max(1, max_pages)):
            query = {"limit": CATEGORY_PAGE_MAX, "cursor": cursor, "include_ui": 1 if include_ui else None}
            page: CategoryPage = yield Op("GET", self._categories, CategoryPage.from_api, query=query, safe=True)
            items.extend(page.items)
            cursor = page.next_cursor if page.has_more else None
            if not cursor:
                break
        return tuple(items)

    def offers(self, category_id: str, include_ui: bool = True) -> Any:
        query = {"category_id": required(category_id, "category_id"), "include_ui": 1 if include_ui else None}
        return self._run(Op("GET", self._offers, Offers.from_api, query=query, safe=True))


class Topups(_Catalog):
    _categories = "topup_categories"
    _offers = "topup_offers"

    def validation_games(self) -> Any:
        return self._run(Op("GET", "validate_id", _list_of(ValidationGame, "items"), safe=True))

    def validate(
        self,
        category_id: str,
        player_id: Optional[str] = None,
        *,
        server_id: Optional[str] = None,
        fields: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        body = {"category_id": required(category_id, "category_id"),
                "fields": player_fields(fields, player_id=player_id, server_id=server_id)}
        return self._run(Op("POST", "validate_id", PlayerCheck.from_api, body=body, safe=True))

    def order(
        self,
        category_id: str,
        offer_id: str,
        player_id: Optional[str] = None,
        *,
        server_id: Optional[str] = None,
        fields: Optional[Mapping[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        category, offer = required(category_id, "category_id"), required(offer_id, "offer_id")
        given = player_fields(fields, player_id=player_id, server_id=server_id)
        key = self._key(idempotency_key)
        op = Op("POST", "topup_order", lambda body: Order.from_api(body).with_key(key),
                body={"category_id": category, "offer_id": offer, "fields": given}, key=key,
                echo={"category_id": category, "offer_id": offer, "player_id": given.get("player_id")})
        return self._run(op)


class GiftCards(_Catalog):
    _categories = "giftcard_categories"
    _offers = "giftcard_offers"

    def cards(self, category_id: str, include_ui: bool = True) -> Any:
        return self.offers(category_id, include_ui)

    def order(
        self,
        category_id: str,
        card_id: str,
        quantity: int = 1,
        *,
        idempotency_key: Optional[str] = None,
        wait_for_codes: bool = True,
    ) -> Any:
        category, card = required(category_id, "category_id"), required(card_id, "card_id")
        count = whole(quantity, "quantity", 1, GIFT_CARD_MAX)
        key = self._key(idempotency_key)
        op = Op("POST", "giftcard_order", lambda body: Order.from_api(body).with_key(key),
                body={"category_id": category, "card_id": card, "quantity": count}, key=key,
                echo={"category_id": category, "offer_id": card})
        checks = self._settings.code_checks if wait_for_codes else 0
        return self._flow(self._codes(op, key, checks, self._settings.code_check_wait))

    def _codes(self, op: Op, key: str, checks: int, wait: float) -> Flow[Order]:
        order: Order = yield op
        for attempt in range(checks):
            if not order.awaiting_codes or not order.id:
                break
            if attempt:
                yield Pause(wait)
            fresh: Order = yield Op("GET", "order", Order.from_api, path_params={"order_id": order.id}, safe=True)
            order = fresh.with_key(key)
        return order


class Orders(_Resource):
    def get(self, order_id_: str) -> Any:
        return self._run(Op("GET", "order", Order.from_api, path_params={"order_id": order_id(order_id_)}, safe=True))

    def list(self, page: int = 1, limit: int = 20) -> Any:
        query = {"page": whole(page, "page", 1, 10**9), "limit": whole(limit, "limit", 1, ORDER_PAGE_MAX)}
        return self._run(Op("GET", "orders", OrderPage.from_api, query=query, safe=True))

    def recent(self, count: int = 100) -> Any:
        return self._flow(self._recent(whole(count, "count", 1, 10**6)))

    def _recent(self, count: int) -> Flow[tuple[Order, ...]]:
        items: list[Order] = []
        page = 1
        while len(items) < count:
            query = {"page": page, "limit": min(ORDER_PAGE_MAX, count - len(items))}
            batch: OrderPage = yield Op("GET", "orders", OrderPage.from_api, query=query, safe=True)
            items.extend(batch.items)
            if not batch.items or not batch.has_more:
                break
            page += 1
        return tuple(items[:count])

    def wait(self, order_id_: str, timeout: float = 120.0, interval: float = 5.0) -> Any:
        return self._flow(self._wait(order_id(order_id_), timeout, max(0.0, interval)))

    def _wait(self, wanted: str, timeout: float, interval: float) -> Flow[Order]:
        deadline = time.monotonic() + timeout
        while True:
            order: Order = yield Op("GET", "order", Order.from_api, path_params={"order_id": wanted}, safe=True)
            if order.status.final and not order.awaiting_codes:
                return order
            if time.monotonic() + interval > deadline:
                raise WaitTimeoutError(text("error.wait_timeout", order_id=wanted, status=order.status,
                                            seconds=timeout), order=order)
            yield Pause(interval)


class Telegram(_Resource):
    def stars_quote(self) -> Any:
        return self._run(Op("GET", "stars_quote", StarsQuote.from_api, safe=True))

    def premium_quote(self) -> Any:
        return self._run(Op("GET", "premium_quote", PremiumQuote.from_api, safe=True))

    def buy_stars(self, username_: str, quantity: int) -> Any:
        body = {"telegram_username": username(username_), "quantity": whole(quantity, "quantity", STARS_MIN, STARS_MAX)}
        return self._run(Op("POST", "stars_buy", Order.from_api, body=body))

    def buy_premium(self, username_: str, months: int) -> Any:
        if months not in PREMIUM_MONTHS or isinstance(months, bool):
            raise InvalidRequestError(text("value.choice", field="months", choices=PREMIUM_MONTHS, value=months))
        body = {"telegram_username": username(username_), "months": months}
        return self._run(Op("POST", "premium_buy", Order.from_api, body=body))


class Steam(_Resource):
    def rates(self) -> Any:
        return self._run(Op("GET", "steam_rates", SteamRates.from_api, safe=True))

    def check_login(self, login: str) -> Any:
        body = {"steamLogin": required(login, "login", 64)}
        return self._run(Op("POST", "steam_login", SteamLogin.from_api, body=body, safe=True))

    def order(
        self,
        login: str,
        amount_: Amount,
        currency: CurrencyLike = SteamCurrency.USD,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        try:
            code = str(SteamCurrency(str(currency).upper()))
        except ValueError:
            choices = tuple(str(item) for item in SteamCurrency)
            raise InvalidRequestError(text("value.choice", field="currency", choices=choices, value=currency)) from None
        value: Decimal = amount(amount_)
        key = self._key(idempotency_key)
        body = {"steamLogin": required(login, "login", 64), "currency": code, "amount": wire(value)}
        return self._run(Op("POST", "steam_order", lambda data: Order.from_api(data).with_key(key), body=body, key=key))


class AccountResource(_Resource):
    def me(self) -> Any:
        return self._run(Op("GET", "me", Account.from_api, safe=True))

    def balance(self) -> Any:
        return self._run(Op("GET", "balance", Balance.from_api, safe=True))

    def webhook(self) -> Any:
        return self._run(Op("GET", "webhook", Webhook.from_api, safe=True))

    def set_webhook(self, url: str) -> Any:
        return self._run(Op("PUT", "webhook", Webhook.from_api, body={"url": https_url(url)}, safe=True))
