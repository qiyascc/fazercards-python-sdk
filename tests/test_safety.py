from __future__ import annotations

import httpx
import pytest

from fazercards_sdk import (
    APIError,
    AuthenticationError,
    BadRequestError,
    FazerCards,
    NotSentError,
    OutcomeUnknownError,
    RateLimitError,
    ServerError,
    TransportError,
)

from .conftest import KEY, gift_order, topup_order


def test_an_order_is_never_resent_after_a_timeout(gw, fc):
    gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(OutcomeUnknownError) as info:
        fc.topups.order("free_fire_cis", "110_diamonds", "1", idempotency_key="k7")
    assert len(gw.requests) == 1 and info.value.idempotency_key == "k7"


@pytest.mark.parametrize("exc", [httpx.RemoteProtocolError("cut"), httpx.ReadError("reset"), httpx.WriteTimeout("w")])
def test_any_ambiguous_failure_on_a_purchase_is_unknown(gw, fc, exc):
    gw.fail(exc)
    with pytest.raises(OutcomeUnknownError):
        fc.telegram.buy_stars("someone", 100)
    assert len(gw.requests) == 1


def test_server_error_on_a_purchase_is_unknown_and_not_retried(gw, fc):
    gw.reply({"message": "boom"}, status=502)
    with pytest.raises(OutcomeUnknownError) as info:
        fc.giftcards.order("playstation_tr", "250_try")
    assert info.value.status_code == 502 and len(gw.requests) == 1


def test_garbage_success_body_on_a_purchase_is_unknown(gw, fc):
    gw.reply(b"<html>ok</html>")
    with pytest.raises(OutcomeUnknownError):
        fc.steam.order("player_1", 5)


def test_connection_refused_is_retried_because_nothing_was_sent(gw, fc):
    gw.fail(httpx.ConnectError("refused")).reply(topup_order())
    assert fc.topups.order("free_fire_cis", "110_diamonds", "123456789").id == "ord-1002"
    assert len(gw.requests) == 2


def test_connection_refused_every_time_is_not_sent(gw, fc):
    for _ in range(3):
        gw.fail(httpx.ConnectError("refused"))
    with pytest.raises(NotSentError):
        fc.telegram.buy_stars("someone", 100)
    assert len(gw.requests) == 3


def test_reads_retry_timeouts_and_server_errors(gw, fc):
    gw.fail(httpx.ReadTimeout("slow")).reply({"x": 1}, status=503)
    gw.reply({"ok": True, "balance": "1", "currency": "USD"})
    assert str(fc.balance().amount) == "1"
    assert len(gw.requests) == 3


def test_reads_give_up(gw, fc):
    for _ in range(3):
        gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(TransportError):
        fc.orders.get("ord-1")


def test_rate_limit_is_waited_out_even_for_purchases(gw, fc):
    waits = []
    fc._sleep = waits.append
    gw.reply({"ok": False, "error": "Too many"}, status=429, headers={"retry-after": "3"}).reply(gift_order())
    assert fc.giftcards.order("playstation_tr", "250_try").codes
    assert waits == [3.0] and len(gw.requests) == 2


def test_rate_limit_that_does_not_end(gw, fc):
    for _ in range(3):
        gw.reply({"ok": False, "error": "Too many"}, status=429, headers={"retry-after": "1"})
    with pytest.raises(RateLimitError) as info:
        fc.balance()
    assert info.value.retry_after == 1.0


def test_rate_limit_headers_are_kept(gw, fc):
    gw.reply({"ok": True, "balance": "1"}, headers={"x-ratelimit-limit": "60", "x-ratelimit-remaining": "59",
                                                    "x-ratelimit-reset": "60"})
    fc.balance()
    assert fc.rate_limit is not None and fc.rate_limit.remaining == 59 and fc.rate_limit.limit == 60


def test_keyed_orders_can_be_resent_once_with_the_same_key(gw):
    client = FazerCards(KEY, resend_keyed_orders=True,
                        http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    client._backoff = lambda attempt: 0.0
    gw.fail(httpx.ReadTimeout("slow")).reply(topup_order())
    client.topups.order("free_fire_cis", "110_diamonds", "123456789", idempotency_key="k1")
    assert [r.headers["idempotency-key"] for r in gw.requests] == ["k1", "k1"]


def test_unkeyed_purchases_are_never_resent_even_when_allowed(gw):
    client = FazerCards(KEY, resend_keyed_orders=True,
                        http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(OutcomeUnknownError):
        client.telegram.buy_stars("someone", 100)
    assert len(gw.requests) == 1


@pytest.mark.parametrize("status,kind", [(400, BadRequestError), (401, AuthenticationError), (500, ServerError)])
def test_errors_by_status(gw, fc, status, kind):
    for _ in range(3):
        gw.reply({"ok": False, "error": "body: must have required property 'category_id'"}, status=status)
    with pytest.raises(kind) as info:
        fc.orders.list()
    assert "category_id" in info.value.message


def test_ok_false_with_200_is_an_error(gw, fc):
    gw.reply({"ok": False, "error": "nope"})
    with pytest.raises(APIError) as info:
        fc.balance()
    assert info.value.message == "nope"


def test_api_key_is_not_in_repr(fc):
    assert KEY not in repr(fc)
