from __future__ import annotations

import pytest

from fazercards_sdk import ConfigurationError, FazerCards, Settings, messages


def test_settings_from_the_environment(monkeypatch):
    monkeypatch.setenv("FAZERCARDS_API_KEY", "env-key")
    monkeypatch.setenv("FAZERCARDS_TIMEOUT", "12")
    monkeypatch.setenv("FAZERCARDS_ENDPOINTS__BALANCE", "/wallet")
    client = FazerCards()
    assert client.settings.timeout == 12 and client.settings.url("balance") == client.settings.base_url + "/wallet"


def test_settings_from_a_file(tmp_path):
    path = tmp_path / "fazercards.toml"
    path.write_text('api_key = "file-key"\nidempotency_prefix = "shop"\n')
    client = FazerCards(config_file=str(path))
    assert client.settings.scoped("k") == "shop:k"


def test_a_key_is_required(monkeypatch):
    monkeypatch.delenv("FAZERCARDS_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        FazerCards()


def test_plain_http_is_refused_outside_localhost():
    with pytest.raises(ConfigurationError):
        FazerCards("k", base_url="http://api.example.com/v2")
    assert FazerCards("k", base_url="http://localhost:8080/v2").settings.base_url == "http://localhost:8080/v2"
    assert FazerCards("k", base_url="http://10.0.0.5/v2", allow_insecure_http=True)


def test_overrides_on_top_of_settings():
    base = Settings(load=False, api_key="a", webhook_secret="s")
    client = FazerCards(settings=base, timeout=5)
    assert client.settings.timeout == 5 and client.settings.webhook_secret.get_secret_value() == "s"


def test_messages_can_be_replaced():
    try:
        messages.use({"error": {"missing_key": "Açar lazımdır"}})
        assert messages.text("error.missing_key") == "Açar lazımdır"
        with pytest.raises(KeyError):
            messages.use({"error": {"nope": "x"}})
    finally:
        messages.reset()
