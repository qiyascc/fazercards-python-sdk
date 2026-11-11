from __future__ import annotations

import httpx
import pytest

from fazercards_sdk import OutcomeUnknownError

from .conftest import gift_order


async def test_async_gift_card_reads_missing_codes_again(gw, afc):
    gw.reply(gift_order(cards=())).reply(gift_order())
    order = await afc.giftcards.order("playstation_tr", "250_try", idempotency_key="gc-9")
    assert order.codes == ("ABCD-1234-EFGH",) and len(gw.requests) == 2


async def test_async_categories_and_balance(gw, afc):
    gw.reply({"ok": True, "kind": "topup", "items": [{"category_id": "a", "name": "A"}],
              "meta": {"total": 1, "limit": 500, "next_cursor": None, "has_more": False}})
    gw.reply({"ok": True, "balance": "2.50", "currency": "USD"})
    assert [c.category_id for c in await afc.topups.all_categories()] == ["a"]
    assert str((await afc.balance()).amount) == "2.50"


async def test_async_purchase_is_not_resent(gw, afc):
    gw.fail(httpx.ReadTimeout("slow"))
    with pytest.raises(OutcomeUnknownError):
        await afc.telegram.buy_premium("someone", 3)
    assert len(gw.requests) == 1


async def test_async_raw_request(gw, afc):
    gw.reply({"ok": True, "login": "shop"})
    assert (await afc.request("GET", "/me"))["login"] == "shop"


async def test_async_context_manager():
    from fazercards_sdk import AsyncFazerCards

    async with AsyncFazerCards("key") as client:
        assert client.settings.base_url == "https://api.fzr.cards/api/v2"
