import pytest

from app.config import Settings


def test_startup_validation_requires_ollama_base_url():
    config = Settings(LLM_PROVIDER="ollama", LLM_BASE_URL="")

    with pytest.raises(ValueError, match="LLM_BASE_URL must be set"):
        config.validate_startup()


def test_startup_validation_accepts_ollama_base_url():
    config = Settings(LLM_PROVIDER="ollama", LLM_BASE_URL=" http://localhost:11434 ")

    config.validate_startup()
    assert config.require_llm_base_url() == "http://localhost:11434"


def test_startup_validation_does_not_require_base_url_for_gemini():
    config = Settings(LLM_PROVIDER="gemini", LLM_BASE_URL="")

    config.validate_startup()
