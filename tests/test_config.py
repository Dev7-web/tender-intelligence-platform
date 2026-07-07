import pytest
from pydantic import ValidationError

from app.config import Settings


STRONG_JWT_SECRET = "test-jwt-secret-value-that-is-at-least-32-chars"


def make_settings(**overrides):
    values = {"JWT_SECRET": STRONG_JWT_SECRET, **overrides}
    return Settings(_env_file=None, **values)


def test_settings_requires_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret", ["", "short-secret", "change-me"])
def test_startup_validation_rejects_weak_jwt_secret(secret):
    config = make_settings(LLM_PROVIDER="gemini", JWT_SECRET=secret)

    with pytest.raises(ValueError, match="JWT_SECRET must be set"):
        config.validate_startup()


def test_startup_validation_accepts_strong_jwt_secret():
    config = make_settings(LLM_PROVIDER="gemini")

    config.validate_startup()
    assert config.require_jwt_secret() == STRONG_JWT_SECRET


def test_startup_validation_requires_ollama_base_url():
    config = make_settings(LLM_PROVIDER="ollama", LLM_BASE_URL="")

    with pytest.raises(ValueError, match="LLM_BASE_URL must be set"):
        config.validate_startup()


def test_startup_validation_accepts_ollama_base_url():
    config = make_settings(LLM_PROVIDER="ollama", LLM_BASE_URL=" http://localhost:11434 ")

    config.validate_startup()
    assert config.require_llm_base_url() == "http://localhost:11434"


def test_startup_validation_does_not_require_base_url_for_gemini():
    config = make_settings(LLM_PROVIDER="gemini", LLM_BASE_URL="")

    config.validate_startup()


def test_settings_ignores_extra_env_entries(tmp_path, monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"JWT_SECRET={STRONG_JWT_SECRET}",
                "LLM_PROVIDER=gemini",
                "OAUTH_REDIRECT_URL=https://example.com/auth/callback",
            ]
        ),
        encoding="utf-8",
    )

    config = Settings(_env_file=env_file)

    assert config.JWT_SECRET == STRONG_JWT_SECRET
