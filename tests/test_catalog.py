from __future__ import annotations

from decimal import Decimal

import pytest

from fazercards_sdk import InvalidRequestError, NotFoundError


def _page(ids, cursor=None, kind="topup", total=3):
    return {
        "ok": True,
        "kind": kind,
        "items": [{"category_id": i, "name": i.title(), "note": "n", "imageurl": f"https://cdn/{i}.png"} for i in ids],
        "meta": {"total": total, "limit": 2, "next_cursor": cursor, "has_more": cursor is not None},
    }


def test_one_page_of_categories(gw, fc):
    gw.reply(_page(["8_ball_pool", "acecraft"], cursor="abc"))
    page = fc.topups.categories(limit=2)
    assert [c.category_id for c in page.items] == ["8_ball_pool", "acecraft"]
    assert page.has_more and page.next_cursor == "abc" and page.total == 3
    assert page.items[0].image_url == "https://cdn/8_ball_pool.png" and page.items[0].kind == "topup"
    assert gw.paths == ["/api/v2/topups"] and gw.queries[0] == {"limit": "2", "include_ui": "1"}
    assert gw.header("x-api-key") == "test_api_key_0001"


def test_all_categories_follows_the_cursor(gw, fc):
    gw.reply(_page(["a", "b"], cursor="next", kind="gift_card")).reply(_page(["c"], kind="gift_card"))
    items = fc.giftcards.all_categories()
    assert [c.category_id for c in items] == ["a", "b", "c"]
    assert gw.paths == ["/api/v2/giftcards", "/api/v2/giftcards"]
    assert gw.queries[1]["cursor"] == "next" and gw.queries[0]["limit"] == "500"


def test_category_limit_is_checked(fc):
    with pytest.raises(InvalidRequestError):
        fc.topups.categories(limit=501)


def test_topup_offers_and_their_fields(gw, fc):
    gw.reply({
        "ok": True, "kind": "topup", "category_id": "free_fire_cis", "name": "Free Fire (CIS)",
        "offers": [{"offer_id": "110_diamonds", "name": "110 Diamonds", "price_usd": "0.7751"}],
        "fields": [{"key": "player_id", "label": "Player ID", "type": "text"}],
        "note": "Region: CIS", "imageurl": "https://cdn/ff.png",
    })
    offers = fc.topups.offers("free_fire_cis")
    offer = offers.get("110_diamonds")
    assert offer is not None and offer.price == Decimal("0.7751") and offer.in_stock
    assert offers.fields[0].key == "player_id" and offers.fields[0].label == "Player ID"
    assert gw.queries[0] == {"category_id": "free_fire_cis", "include_ui": "1"}


def test_gift_card_offers_carry_stock_and_limits(gw, fc):
    gw.reply({
        "ok": True, "kind": "gift_card", "category_id": "playstation_tr", "name": "PlayStation (TR)",
        "offers": [
            {"card_id": "250_try", "name": "250 TRY", "price_usd": "4.8628", "stock": 152,
             "min_order_quantity": 1, "max_order_quantity": 100},
            {"card_id": "5000_try", "name": "5000 TRY", "price_usd": "97.2558", "stock": 0,
             "min_order_quantity": 1, "max_order_quantity": 2},
        ],
    })
    cards = fc.giftcards.cards("playstation_tr")
    assert gw.paths == ["/api/v2/giftcards/cards"]
    assert cards.offers[0].id == "250_try" and cards.offers[0].max_quantity == 100
    assert not cards.offers[1].in_stock


def test_unknown_category_is_not_found(gw, fc):
    gw.reply({"ok": False, "error": "Unknown or unavailable category_id."}, status=404)
    with pytest.raises(NotFoundError) as info:
        fc.topups.offers("mobile_legends")
    assert info.value.message == "Unknown or unavailable category_id." and info.value.status_code == 404


def test_player_check(gw, fc):
    gw.reply({"ok": True, "category_id": "free_fire", "valid": True, "player_name": "Hero", "player_id": "123456789",
              "region": "RU"})
    check = fc.topups.validate("free_fire", "123456789")
    assert check.valid is True and check.player_name == "Hero" and check.region == "RU"
    assert gw.body() == {"category_id": "free_fire", "fields": {"player_id": "123456789"}}


def test_player_check_with_a_server(gw, fc):
    gw.reply({"ok": True, "valid": False, "player_name": None})
    check = fc.topups.validate("mlbb", "1", server_id="2001")
    assert check.valid is False
    assert gw.body()["fields"] == {"player_id": "1", "server_id": "2001"}


def test_validation_games(gw, fc):
    gw.reply({"ok": True, "kind": "topup", "items": [
        {"category_id": "pubg_mobile", "name": "PUBG Mobile", "fields": [{"key": "player_id", "label": "Player ID"}]},
    ]})
    games = fc.topups.validation_games()
    assert games[0].category_id == "pubg_mobile" and games[0].fields[0].key == "player_id"
    assert gw.requests[0].method == "GET" and gw.paths == ["/api/v2/topups/validate-id"]
