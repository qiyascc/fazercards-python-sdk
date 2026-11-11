from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Mapping, Optional, TypeVar

import httpx

from .config import Settings, load_settings
from .errors import (
    APIError,
    KeyCollisionError,
    NotSentError,
    OutcomeUnknownError,
    RateLimitError,
    TransportError,
    for_status,
)
from .messages import text
from .models import RateLimit

T = TypeVar("T")

NOT_SENT = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout, httpx.UnsupportedProtocol)
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


@dataclass
class Op:
    method: str
    endpoint: str
    parse: Callable[[Any], Any] = lambda body: body
    query: Optional[dict[str, Any]] = None
    body: Optional[dict[str, Any]] = None
    path_params: Mapping[str, Any] = field(default_factory=dict)
    safe: bool = False
    key: Optional[str] = None
    echo: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Pause:
    seconds: float


Step = Any
Flow = Generator[Step, Any, T]


class Outcome:
    def __init__(self, value: Any = None, error: Optional[Exception] = None, wait: Optional[float] = None) -> None:
        self.value = value
        self.error = error
        self.wait = wait


def _number(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _echo_mismatch(body: Any, expected: Mapping[str, Any]) -> Optional[str]:
    order = body.get("order", body) if isinstance(body, Mapping) else None
    if not isinstance(order, Mapping):
        return None
    given = order.get("fields")
    fields: Mapping[str, Any] = given if isinstance(given, Mapping) else {}
    actual = {
        "category_id": order.get("category_id"),
        "offer_id": order.get("offer_id") or order.get("card_id"),
        "player_id": fields.get("player_id"),
    }
    for name, value in expected.items():
        seen = actual.get(name)
        if value not in (None, "") and seen is not None and str(seen) != str(value):
            return str(order.get("id") or order.get("order_id") or "?")
    return None


class Engine:
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        settings: Optional[Settings] = None,
        config_file: Optional[str] = None,
        **overrides: Any,
    ) -> None:
        if settings is None:
            settings = load_settings(config_file, api_key=api_key, **overrides)
        elif api_key or overrides:
            current = settings.model_dump()
            current["api_key"] = settings.api_key.get_secret_value()
            current["webhook_secret"] = settings.webhook_secret.get_secret_value()
            changes = {k: v for k, v in dict(overrides, api_key=api_key).items() if v is not None}
            settings = load_settings(None, **{**current, **changes})
        self.settings = settings
        settings.check_transport()
        self._api_key = settings.key()
        self.rate_limit: Optional[RateLimit] = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self.settings.base_url!r})"

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(self.settings.timeout, connect=self.settings.connect_timeout)

    def _headers(self, op: Op) -> dict[str, str]:
        headers = {
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": self.settings.resolved_user_agent(),
        }
        if op.key:
            headers["Idempotency-Key"] = op.key
        return headers

    def _request_args(self, op: Op) -> dict[str, Any]:
        args: dict[str, Any] = {"headers": self._headers(op)}
        if op.method != "GET":
            args["json"] = op.body or {}
        return args

    def _backoff(self, attempt: int) -> float:
        base = self.settings.backoff_base
        return min(self.settings.backoff_cap, base * (2**attempt)) + random.uniform(0, base / 2)

    def _resend(self, op: Op, attempt: int) -> bool:
        return bool(op.key) and self.settings.resend_keyed_orders and attempt == 0

    def _remember_limits(self, response: httpx.Response) -> None:
        headers = response.headers
        if "x-ratelimit-limit" not in headers:
            return
        limit, remaining = _number(headers.get("x-ratelimit-limit")), _number(headers.get("x-ratelimit-remaining"))
        self.rate_limit = RateLimit(
            int(limit) if limit is not None else None,
            int(remaining) if remaining is not None else None,
            _number(headers.get("x-ratelimit-reset")),
        )

    def _on_exception(self, op: Op, exc: Exception, attempt: int) -> Outcome:
        path = self.settings.path(op.endpoint, **op.path_params)
        can_retry = attempt < self.settings.max_retries
        if isinstance(exc, NOT_SENT):
            if can_retry:
                return Outcome(wait=self._backoff(attempt))
            return Outcome(error=NotSentError(text("error.connect", error=exc), path=path, idempotency_key=op.key))
        if op.safe:
            if can_retry:
                return Outcome(wait=self._backoff(attempt))
            return Outcome(error=TransportError(text("error.timeout", error=exc), path=path, idempotency_key=op.key))
        if self._resend(op, attempt):
            return Outcome(wait=self._backoff(attempt))
        return Outcome(error=OutcomeUnknownError(text("error.unknown_outcome", reason=type(exc).__name__), path=path,
                                                 idempotency_key=op.key))

    def _on_response(self, op: Op, response: httpx.Response, attempt: int) -> Outcome:
        self._remember_limits(response)
        path = self.settings.path(op.endpoint, **op.path_params)
        status = response.status_code
        can_retry = attempt < self.settings.max_retries
        if status == 429 and can_retry:
            hint = _number(response.headers.get("retry-after")) or _number(response.headers.get("x-ratelimit-reset"))
            return Outcome(wait=min(self.settings.backoff_cap, hint) if hint is not None else self._backoff(attempt))
        if status in RETRY_STATUSES and status != 429:
            if op.safe and can_retry:
                return Outcome(wait=self._backoff(attempt))
            if not op.safe:
                if self._resend(op, attempt):
                    return Outcome(wait=self._backoff(attempt))
                return Outcome(error=OutcomeUnknownError(text("error.unknown_outcome", reason=f"HTTP {status}"),
                                                         status_code=status, path=path, idempotency_key=op.key))
        try:
            body = response.json()
        except ValueError:
            snippet = response.text[:200]
            if status < 400 and not op.safe:
                return Outcome(error=OutcomeUnknownError(text("error.body", body=snippet), status_code=status,
                                                         path=path, idempotency_key=op.key))
            return Outcome(error=for_status(status)(text("error.body", body=snippet), status_code=status,
                                                    body=snippet, path=path))
        refused = isinstance(body, Mapping) and body.get("ok") is False
        if status >= 400 or refused:
            message = (body.get("message") or body.get("error")) if isinstance(body, Mapping) else None
            kind = for_status(status) if status >= 400 else APIError
            error_args: dict[str, Any] = {"status_code": status, "body": body, "path": path}
            if kind is RateLimitError:
                error_args["retry_after"] = _number(response.headers.get("retry-after"))
            return Outcome(error=kind(str(message or text("error.refused")), **error_args))
        if op.key and op.echo:
            other = _echo_mismatch(body, op.echo)
            if other is not None:
                return Outcome(error=KeyCollisionError(text("error.collision", idempotency_key=op.key, order_id=other),
                                                       idempotency_key=op.key, order=body))
        return Outcome(value=op.parse(body))


class SyncEngine(Engine):
    def __init__(self, *args: Any, http_client: Optional[httpx.Client] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=self._timeout())

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def _run(self, op: Op) -> Any:
        url = self.settings.url(op.endpoint, op.query, **op.path_params)
        args = self._request_args(op)
        attempt = 0
        while True:
            try:
                response = self._http.request(op.method, url, **args)
            except httpx.HTTPError as exc:
                outcome = self._on_exception(op, exc, attempt)
            else:
                outcome = self._on_response(op, response, attempt)
            if outcome.wait is not None:
                self._sleep(outcome.wait)
                attempt += 1
                continue
            if outcome.error is not None:
                raise outcome.error
            return outcome.value

    def _flow(self, flow: Flow[T]) -> T:
        reply: Any = None
        while True:
            try:
                step = flow.send(reply)
            except StopIteration as done:
                result: T = done.value
                return result
            if isinstance(step, Pause):
                self._sleep(step.seconds)
                reply = None
            else:
                reply = self._run(step)


class AsyncEngine(Engine):
    def __init__(self, *args: Any, http_client: Optional[httpx.AsyncClient] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=self._timeout())

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self: T) -> T:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            await asyncio.sleep(seconds)

    async def _run(self, op: Op) -> Any:
        url = self.settings.url(op.endpoint, op.query, **op.path_params)
        args = self._request_args(op)
        attempt = 0
        while True:
            try:
                response = await self._http.request(op.method, url, **args)
            except httpx.HTTPError as exc:
                outcome = self._on_exception(op, exc, attempt)
            else:
                outcome = self._on_response(op, response, attempt)
            if outcome.wait is not None:
                await self._sleep(outcome.wait)
                attempt += 1
                continue
            if outcome.error is not None:
                raise outcome.error
            return outcome.value

    async def _flow(self, flow: Flow[T]) -> T:
        reply: Any = None
        while True:
            try:
                step = flow.send(reply)
            except StopIteration as done:
                result: T = done.value
                return result
            if isinstance(step, Pause):
                await self._sleep(step.seconds)
                reply = None
            else:
                reply = await self._run(step)
