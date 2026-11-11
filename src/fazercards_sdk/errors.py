from __future__ import annotations

from typing import Any, Optional


class FazerCardsError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(FazerCardsError):
    pass


class InvalidRequestError(FazerCardsError, ValueError):
    pass


class SignatureError(FazerCardsError):
    pass


class TransportError(FazerCardsError):
    def __init__(self, message: str, *, path: str = "", idempotency_key: Optional[str] = None) -> None:
        super().__init__(message)
        self.path = path
        self.idempotency_key = idempotency_key


class NotSentError(TransportError):
    pass


class OutcomeUnknownError(TransportError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.status_code = status_code


class APIError(FazerCardsError):
    def __init__(self, message: str, *, status_code: int, body: Any = None, path: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.path = path

    def __str__(self) -> str:
        return f"[{self.status_code}] {self.message}"


class BadRequestError(APIError):
    pass


class AuthenticationError(APIError):
    pass


class NotFoundError(APIError):
    pass


class ConflictError(APIError):
    pass


class RateLimitError(APIError):
    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIError):
    pass


class KeyCollisionError(FazerCardsError):
    def __init__(self, message: str, *, idempotency_key: str, order: Any = None) -> None:
        super().__init__(message)
        self.idempotency_key = idempotency_key
        self.order = order


class WaitTimeoutError(FazerCardsError):
    def __init__(self, message: str, *, order: Any = None) -> None:
        super().__init__(message)
        self.order = order


def for_status(status: int) -> type[APIError]:
    if status in (401, 403):
        return AuthenticationError
    if status == 404:
        return NotFoundError
    if status == 409:
        return ConflictError
    if status == 429:
        return RateLimitError
    if status >= 500:
        return ServerError
    if status >= 400:
        return BadRequestError
    return APIError
