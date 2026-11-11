from __future__ import annotations

from enum import Enum
from typing import Any


class _Text(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class OrderStatus(_Text):
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    SUCCESS = "success"
    FAILED = "failed"
    REFUND = "refund"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    CANCELED = "canceled"
    ERROR = "error"
    UNKNOWN = "unknown"

    @classmethod
    def of(cls, value: Any) -> OrderStatus:
        text = str(value or "").strip().lower()
        try:
            return cls(text)
        except ValueError:
            return cls.UNKNOWN

    @property
    def delivered(self) -> bool:
        return self in _DELIVERED

    @property
    def failed(self) -> bool:
        return self in _FAILED

    @property
    def in_flight(self) -> bool:
        return self in _IN_FLIGHT

    @property
    def final(self) -> bool:
        return self.delivered or self.failed


_DELIVERED = frozenset({OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.SUCCESS})
_FAILED = frozenset(
    {
        OrderStatus.FAILED,
        OrderStatus.REFUND,
        OrderStatus.REFUNDED,
        OrderStatus.CANCELLED,
        OrderStatus.CANCELED,
        OrderStatus.ERROR,
    }
)
_IN_FLIGHT = frozenset({OrderStatus.CREATED, OrderStatus.PENDING, OrderStatus.PROCESSING})


class OrderKind(_Text):
    TOPUP = "topup"
    GIFT_CARD = "gift_card"
    TELEGRAM_STARS = "telegram_stars"
    TELEGRAM_PREMIUM = "telegram_premium"
    STEAM_TOPUP = "steam_topup"
    UNKNOWN = "unknown"

    @classmethod
    def of(cls, value: Any) -> OrderKind:
        text = str(value or "").strip().lower()
        try:
            return cls(text)
        except ValueError:
            return cls.UNKNOWN


class SteamCurrency(_Text):
    USD = "USD"
    RUB = "RUB"
    UAH = "UAH"
    KZT = "KZT"


PREMIUM_MONTHS = (3, 6, 12)
