from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote, urlencode, urlsplit

from goodconf import Field, GoodConf, GoodConfConfigDict
from pydantic import BaseModel, SecretStr, field_validator

from ._version import __version__
from .errors import ConfigurationError
from .messages import text

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class Endpoints(BaseModel):
    me: str = "/me"
    balance: str = "/balance"
    webhook: str = "/account/webhook"
    topup_categories: str = "/topups"
    topup_offers: str = "/topups/offers"
    topup_order: str = "/topups/order"
    validate_id: str = "/topups/validate-id"
    giftcard_categories: str = "/giftcards"
    giftcard_offers: str = "/giftcards/cards"
    giftcard_order: str = "/giftcards/order"
    orders: str = "/orders"
    order: str = "/orders/{order_id}"
    stars_quote: str = "/telegram/stars"
    stars_buy: str = "/telegram/stars/buy"
    premium_quote: str = "/telegram/premium"
    premium_buy: str = "/telegram/premium/buy"
    steam_rates: str = "/steam-topup/rates"
    steam_login: str = "/steam-topup/check-login"
    steam_order: str = "/steam-topup/order"


class Settings(GoodConf):
    model_config = GoodConfConfigDict(
        env_prefix="FAZERCARDS_",
        file_env_var="FAZERCARDS_CONFIG",
        default_files=["fazercards.toml", "fazercards.yaml", "fazercards.yml", "fazercards.json"],
        extra="ignore",
        env_nested_delimiter="__",
    )

    api_key: SecretStr = Field(default=SecretStr(""), description=text("settings.api_key"))
    base_url: str = Field(default="https://api.fzr.cards/api/v2", description=text("settings.base_url"))
    endpoints: Endpoints = Field(default_factory=Endpoints, description=text("settings.endpoints"))
    webhook_secret: SecretStr = Field(default=SecretStr(""), description=text("settings.webhook_secret"))
    idempotency_prefix: str = Field(default="", description=text("settings.idempotency_prefix"))
    timeout: float = Field(default=30.0, gt=0, description=text("settings.timeout"))
    connect_timeout: float = Field(default=10.0, gt=0, description=text("settings.connect_timeout"))
    max_retries: int = Field(default=2, ge=0, le=10, description=text("settings.max_retries"))
    backoff_base: float = Field(default=0.5, ge=0, description=text("settings.backoff_base"))
    backoff_cap: float = Field(default=8.0, ge=0, description=text("settings.backoff_cap"))
    resend_keyed_orders: bool = Field(default=False, description=text("settings.resend_keyed_orders"))
    code_checks: int = Field(default=3, ge=0, le=20, description=text("settings.code_checks"))
    code_check_wait: float = Field(default=1.0, ge=0, description=text("settings.code_check_wait"))
    user_agent: str = Field(default="fazercards-python-sdk/{version}", description=text("settings.user_agent"))
    allow_insecure_http: bool = Field(default=False, description=text("settings.allow_insecure_http"))

    @field_validator("base_url")
    @classmethod
    def _base_url(cls, value: str) -> str:
        parts = urlsplit(value.strip())
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError(text("error.base_url", url=value))
        return value.strip().rstrip("/")

    def check_transport(self) -> None:
        parts = urlsplit(self.base_url)
        if parts.scheme == "https" or self.allow_insecure_http or parts.hostname in LOCAL_HOSTS:
            return
        raise ConfigurationError(text("error.insecure", url=self.base_url))

    def path(self, endpoint: str, **params: Any) -> str:
        template = endpoint if endpoint.startswith("/") else getattr(self.endpoints, endpoint)
        return str(template.format(**{k: quote(str(v), safe="") for k, v in params.items()}))

    def url(self, endpoint: str, query: Optional[dict[str, Any]] = None, **params: Any) -> str:
        address = self.base_url + self.path(endpoint, **params)
        given = {k: v for k, v in (query or {}).items() if v is not None and v != ""}
        return f"{address}?{urlencode(given)}" if given else address

    def resolved_user_agent(self) -> str:
        return self.user_agent.replace("{version}", __version__)

    def key(self) -> str:
        value = self.api_key.get_secret_value().strip()
        if not value:
            raise ConfigurationError(text("error.missing_key"))
        return value

    def scoped(self, key: str) -> str:
        return f"{self.idempotency_prefix}:{key}" if self.idempotency_prefix else key


Settings.__doc__ = text("settings.description")


def load_settings(config_file: Optional[str] = None, **overrides: Any) -> Settings:
    given = {key: value for key, value in overrides.items() if value is not None}
    return Settings(load=True, config_file=config_file, **given)
