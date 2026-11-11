from __future__ import annotations

import json
from typing import Any, Callable, Union

import httpx
import pytest

from fazercards_sdk import AsyncFazerCards, FazerCards

KEY = "test_api_key_0001"
SECRET = "test_webhook_secret"

Reply = Union[httpx.Response, Exception, Callable[[httpx.Request], httpx.Response]]


def gift_order(status: str = "completed", cards: Any = ("ABCD-1234-EFGH",), order_id: str = "ord-1001") -> dict:
    return {
        "ok": True,
        "order": {
            "title": "PlayStation (TR) • 250 TRY • 1",
            "id": order_id,
            "kind": "gift_card",
            "category_id": "playstation_tr",
            "card_id": "250_try",
            "offer_name": "250 TRY",
            "category_name": "PlayStation (TR)",
            "quantity": 1,
            "price_usd_per_unit": "4.8628",
            "total_usd": "4.8628",
            "status": status,
            "fail_reason": None,
            "cards": list(cards),
            "status_history": [
                {"status": "created", "at": "2026-11-11T07:36:55.189Z"},
                {"status": status, "at": "2026-11-11T07:36:55.804Z"},
            ],
            "created_at": "2026-11-11T07:36:55.189Z",
            "completed_at": "2026-11-11T07:36:55.804Z",
        },
    }


def topup_order(status: str = "processing", player_id: str = "123456789", offer_id: str = "110_diamonds") -> dict:
    return {
        "ok": True,
        "order": {
            "title": f"Free Fire (CIS) • 110 Diamonds • {player_id}",
            "id": "ord-1002",
            "kind": "topup",
            "category_id": "free_fire_cis",
            "offer_id": offer_id,
            "offer_name": "110 Diamonds",
            "category_name": "Free Fire (CIS)",
            "fields": {"player_id": player_id},
            "price_usd": "0.7751",
            "total_usd": "0.7751",
            "status": status,
            "fail_reason": None,
            "status_history": [{"status": "created", "at": "2026-11-11T05:45:07.851Z"}],
            "created_at": "2026-11-11T05:45:07.851Z",
            "completed_at": None,
        },
    }


class Gateway:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.replies: list[Reply] = []

    def reply(self, body: Any = None, status: int = 200, headers: Any = None) -> Gateway:
        content = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.replies.append(httpx.Response(status, content=content, headers=headers))
        return self

    def fail(self, exc: Exception) -> Gateway:
        self.replies.append(exc)
        return self

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        reply = self.replies.pop(0) if self.replies else httpx.Response(200, json={"ok": True})
        if isinstance(reply, Exception):
            raise reply
        if callable(reply):
            return reply(request)
        return reply

    def body(self, index: int = -1) -> dict[str, Any]:
        return dict(json.loads(self.requests[index].content.decode()))

    def header(self, name: str, index: int = -1) -> str:
        return str(self.requests[index].headers.get(name, ""))

    @property
    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    @property
    def queries(self) -> list[dict[str, str]]:
        return [dict(r.url.params) for r in self.requests]


@pytest.fixture
def gw() -> Gateway:
    return Gateway()


def _quiet(client: Any) -> Any:
    client._backoff = lambda attempt: 0.0
    client._sleep = (lambda seconds: None) if isinstance(client, FazerCards) else _no_wait
    return client


async def _no_wait(seconds: float) -> None:
    return None


@pytest.fixture
def fc(gw: Gateway) -> FazerCards:
    client = FazerCards(KEY, webhook_secret=SECRET, max_retries=2,
                        http_client=httpx.Client(transport=httpx.MockTransport(gw)))
    return _quiet(client)


@pytest.fixture
def afc(gw: Gateway) -> AsyncFazerCards:
    client = AsyncFazerCards(KEY, webhook_secret=SECRET, max_retries=2,
                             http_client=httpx.AsyncClient(transport=httpx.MockTransport(gw)))
    return _quiet(client)
