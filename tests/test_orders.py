from __future__ import annotations

from datetime import timezone
from decimal import Decimal

import pytest

from fazercards_sdk import (
    FazerCards,
    InvalidRequestError,
    KeyCollisionError,
    OrderKind,
    OrderStatus,
    WaitTimeoutError,
)

from .conftest import KEY, gift_order, topup_order


def test_topup_order_sends_the_fields_and_an_idempotency_key(gw, fc):
    gw.reply(topup_order())
    order = fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="GNET-1-1")
    assert gw.paths == ["/api/v2/topups/order"]
    assert gw.body() == {"category_id": "free_fire_cis", "offer_id": "110_diamonds",
                         "fields": {"player_id": "123456789"}}
    assert gw.header("idempotency-key") == "GNET-1-1" and order.idempotency_key == "GNET-1-1"
    assert order.kind is OrderKind.TOPUP and order.status is OrderStatus.PROCESSING and order.in_flight
    assert order.total == Decimal("0.7751") and order.fields == {"player_id": "123456789"}


def test_a_key_is_made_when_none_is_given(gw, fc):
    gw.reply(topup_order())
    order = fc.topups.order("free_fire_cis", "110_diamonds", "123456789")
    assert len(gw.header("idempotency-key")) == 32 and order.idempotency_key == gw.header("idempotency-key")


def test_the_prefix_keeps_two_shops_apart(gw):
    import httpx

    client = FazerCards(KEY, idempotency_prefix="shop-a",
                        http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    gw.reply(topup_order())
    client.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="k1")
    assert gw.header("idempotency-key") == "shop-a:k1"


def test_an_old_order_behind_a_reused_key_is_refused(gw, fc):
    gw.reply(topup_order(player_id="111"))
    with pytest.raises(KeyCollisionError) as info:
        fc.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="k1")
    assert info.value.idempotency_key == "k1"


def test_topup_needs_a_player(fc):
    with pytest.raises(InvalidRequestError):
        fc.topups.order("free_fire_cis", "110_diamonds")


def test_gift_card_codes_come_back(gw, fc):
    gw.reply(gift_order())
    order = fc.giftcards.order("playstation_tr", "250_try", 1, idempotency_key="gc-1")
    assert order.codes == ("ABCD-1234-EFGH",) and order.delivered and not order.awaiting_codes
    assert gw.body() == {"category_id": "playstation_tr", "card_id": "250_try", "quantity": 1}
    assert order.unit_price == Decimal("4.8628")
    assert order.completed_at is not None and order.completed_at.tzinfo == timezone.utc
    assert [step.status for step in order.history] == [OrderStatus.CREATED, OrderStatus.COMPLETED]


def test_completed_without_codes_is_read_again(gw, fc):
    gw.reply(gift_order(cards=())).reply(gift_order())
    order = fc.giftcards.order("playstation_tr", "250_try", idempotency_key="gc-2")
    assert order.codes == ("ABCD-1234-EFGH",) and order.idempotency_key == "gc-2"
    assert gw.paths == ["/api/v2/giftcards/order", "/api/v2/orders/ord-1001"]


def test_codes_that_never_come_leave_the_order_flagged(gw, fc):
    for _ in range(4):
        gw.reply(gift_order(cards=()))
    order = fc.giftcards.order("playstation_tr", "250_try")
    assert order.awaiting_codes and len(gw.requests) == 4


def test_waiting_for_codes_can_be_turned_off(gw, fc):
    gw.reply(gift_order(cards=()))
    assert fc.giftcards.order("playstation_tr", "250_try", wait_for_codes=False).awaiting_codes
    assert len(gw.requests) == 1


def test_cards_given_as_objects_are_read(gw, fc):
    gw.reply(gift_order(cards=[{"code": "AAAA", "pin": "1234"}, {"serial": "S1"}]))
    assert fc.giftcards.order("playstation_tr", "250_try", 2).codes == ("AAAA / 1234", "S1")


@pytest.mark.parametrize("quantity", [0, 101, True, 1.5])
def test_gift_card_quantity_is_checked(fc, quantity):
    with pytest.raises(InvalidRequestError):
        fc.giftcards.order("playstation_tr", "250_try", quantity)


def test_get_order(gw, fc):
    gw.reply(gift_order())
    assert fc.orders.get("ord-1001").id == "ord-1001"
    assert gw.paths == ["/api/v2/orders/ord-1001"]


@pytest.mark.parametrize("bad", ["", "  ", "ord-1/../balance", "ord-1?x=1"])
def test_order_id_is_checked_before_sending(gw, fc, bad):
    with pytest.raises(InvalidRequestError):
        fc.orders.get(bad)
    assert gw.requests == []


def test_failed_order_keeps_its_reason(gw, fc):
    body = topup_order(status="refund")
    body["order"]["fail_reason"] = "Player not found"
    gw.reply(body)
    order = fc.orders.get("ord-1002")
    assert order.failed and order.status.final and order.fail_reason == "Player not found"


def test_steam_and_telegram_orders_use_camel_case(gw, fc):
    gw.reply({"ok": True, "order": {
        "id": "ord-1003", "kind": "steam_topup", "status": "completed", "amountUsd": "19.0000",
        "chargedUsd": "18.3255", "failReason": None, "createdAt": "2026-11-10T09:12:02.397Z",
        "completedAt": "2026-11-10T09:13:40.733Z",
        "statusHistory": [{"status": "processing", "at": "2026-11-10T09:12:21.542Z"}],
    }})
    order = fc.orders.get("ord-1003")
    assert order.kind is OrderKind.STEAM_TOPUP and order.total == Decimal("18.3255")
    assert order.created_at is not None and order.history[0].status is OrderStatus.PROCESSING


def test_order_list_pages(gw, fc):
    gw.reply({"ok": True, "items": [gift_order()["order"]], "total": 3, "page": 1, "limit": 1})
    page = fc.orders.list(limit=1)
    assert page.has_more and page.items[0].codes == ("ABCD-1234-EFGH",)
    assert gw.queries[0] == {"page": "1", "limit": "1"}
    with pytest.raises(InvalidRequestError):
        fc.orders.list(limit=101)


def test_recent_orders_walk_the_pages(gw, fc):
    one = gift_order()["order"]
    gw.reply({"ok": True, "items": [one] * 100, "total": 150, "page": 1, "limit": 100})
    gw.reply({"ok": True, "items": [one] * 50, "total": 150, "page": 2, "limit": 50})
    assert len(fc.orders.recent(150)) == 150
    assert gw.queries == [{"page": "1", "limit": "100"}, {"page": "2", "limit": "50"}]


def test_wait_returns_when_the_order_is_final(gw, fc):
    gw.reply(topup_order()).reply(topup_order(status="completed"))
    assert fc.orders.wait("ord-1002", timeout=60, interval=1).delivered
    assert len(gw.requests) == 2


def test_wait_gives_up(gw, fc):
    gw.reply(topup_order())
    with pytest.raises(WaitTimeoutError) as info:
        fc.orders.wait("ord-1002", timeout=0, interval=1)
    assert info.value.order.in_flight


def test_telegram_stars(gw, fc):
    gw.reply({"ok": True, "order": {"id": "ord-1004", "kind": "telegram_stars", "status": "processing",
                                    "stars_quantity": 100, "chargedUsd": "1.5263"}})
    order = fc.telegram.buy_stars("@someone", 100)
    assert gw.body() == {"telegram_username": "someone", "quantity": 100}
    assert order.quantity == 100 and order.kind is OrderKind.TELEGRAM_STARS
    assert gw.header("idempotency-key") == ""


@pytest.mark.parametrize("name,quantity", [("someone", 49), ("someone", 100001), ("a b", 100), ("", 100)])
def test_telegram_stars_input_is_checked(fc, name, quantity):
    with pytest.raises(InvalidRequestError):
        fc.telegram.buy_stars(name, quantity)


def test_telegram_premium(gw, fc):
    gw.reply({"ok": True, "order": {"id": "ord-9", "kind": "telegram_premium", "status": "processing"}})
    fc.telegram.buy_premium("someone", 6)
    assert gw.body() == {"telegram_username": "someone", "months": 6}
    with pytest.raises(InvalidRequestError):
        fc.telegram.buy_premium("someone", 4)


def test_quotes(gw, fc):
    gw.reply({"ok": True, "kind": "telegram_stars", "price_per_star": "0.0152625", "min_amount": 50,
              "max_amount": 100000, "rates_updated_at": "2026-11-11T07:36:11.004Z"})
    gw.reply({"ok": True, "kind": "telegram_premium", "plans": [{"months": 3, "price_usd": "12.1999"},
                                                              {"months": 12, "price_usd": "29.0000"}]})
    stars = fc.telegram.stars_quote()
    assert stars.price(100) == Decimal("1.52625") and stars.min_amount == 50
    premium = fc.telegram.premium_quote()
    plan = premium.plan(12)
    assert plan is not None and plan.price == Decimal("29.0000") and premium.plan(6) is None


def test_steam(gw, fc):
    gw.reply({"ok": True, "base": "USD", "rates": {"USD": 1, "RUB": 83.06307}, "updated_at": "2026-11-11T07:46:15Z"})
    gw.reply({"ok": True, "can_refill": True, "unverified": False})
    gw.reply({"ok": True, "can_refill": False, "unverified": True})
    gw.reply({"ok": True, "order": {"id": "ord-5", "kind": "steam_topup", "status": "created"}})
    rates = fc.steam.rates()
    assert rates.convert(Decimal("10"), "rub") == Decimal("830.6307")
    assert fc.steam.check_login("player_1").valid is True
    assert fc.steam.check_login("player_2").valid is None
    order = fc.steam.order("player_1", "19.50", "usd", idempotency_key="st-1")
    assert gw.body() == {"steamLogin": "player_1", "currency": "USD", "amount": "19.50"}
    assert order.idempotency_key == "st-1" and gw.header("idempotency-key") == "st-1"


@pytest.mark.parametrize("amount,currency", [("0", "USD"), ("1.005", "USD"), (True, "USD"), ("5", "EUR")])
def test_steam_order_input_is_checked(gw, fc, amount, currency):
    with pytest.raises(InvalidRequestError):
        fc.steam.order("player_1", amount, currency)
    assert gw.requests == []


def test_account(gw, fc):
    gw.reply({"ok": True, "balance": "19.4899", "currency": "USD"})
    gw.reply({"ok": True, "login": "shop", "plan": "gold", "planExpiresAt": "2026-11-15T14:00:12.392Z",
              "summary": {"totalSpent": "8741.1564", "totalOrders": 1822}})
    balance = fc.balance()
    assert balance.amount == Decimal("19.4899") and balance.currency == "USD"
    me = fc.account.me()
    assert me.plan == "gold" and me.total_orders == 1822 and me.total_spent == Decimal("8741.1564")


def test_webhook_settings(gw, fc):
    hook = {"url": "https://shop.example/hook", "enabled": True, "consecutive_failures": 0}
    gw.reply({"ok": True, "webhook": hook}).reply({"ok": True, "webhook": hook})
    assert fc.account.webhook().enabled
    assert fc.account.set_webhook("https://shop.example/hook").url == "https://shop.example/hook"
    assert gw.requests[1].method == "PUT" and gw.body() == {"url": "https://shop.example/hook"}
    with pytest.raises(InvalidRequestError):
        fc.account.set_webhook("http://shop.example/hook")
