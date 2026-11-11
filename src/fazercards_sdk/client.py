from __future__ import annotations

from typing import Any, Mapping, Optional

from ._core import AsyncEngine, Op, SyncEngine
from .models import WebhookEvent
from .resources import AccountResource, GiftCards, Orders, Steam, Telegram, Topups
from .webhooks import Payload, header, verify_webhook


class _Namespaces:
    settings: Any

    def _mount(self) -> None:
        self.account = AccountResource(self)
        self.topups = Topups(self)
        self.giftcards = GiftCards(self)
        self.orders = Orders(self)
        self.telegram = Telegram(self)
        self.steam = Steam(self)

    def verify_webhook(self, payload: Payload, signature: str = "", *,
                       headers: Optional[Mapping[str, Any]] = None) -> WebhookEvent:
        given = signature or (header(headers) if headers is not None else "")
        return verify_webhook(self.settings.webhook_secret.get_secret_value(), payload, given)

    @staticmethod
    def _raw(method: str, path: str, body: Optional[Mapping[str, Any]], safe: Optional[bool],
             idempotency_key: Optional[str]) -> Op:
        verb = method.upper()
        return Op(verb, path if path.startswith("/") else f"/{path}", body=dict(body) if body is not None else None,
                  safe=verb == "GET" if safe is None else safe, key=idempotency_key)


class FazerCards(SyncEngine, _Namespaces):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._mount()

    def balance(self) -> Any:
        return self.account.balance()

    def request(self, method: str, path: str, body: Optional[Mapping[str, Any]] = None, *,
                safe: Optional[bool] = None, idempotency_key: Optional[str] = None) -> Any:
        return self._run(self._raw(method, path, body, safe, idempotency_key))


class AsyncFazerCards(AsyncEngine, _Namespaces):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._mount()

    async def balance(self) -> Any:
        return await self.account.balance()

    async def request(self, method: str, path: str, body: Optional[Mapping[str, Any]] = None, *,
                      safe: Optional[bool] = None, idempotency_key: Optional[str] = None) -> Any:
        return await self._run(self._raw(method, path, body, safe, idempotency_key))
