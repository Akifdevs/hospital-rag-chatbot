import os
import pytest
from generation.client import (
    get_llm_credentials,
    create_llm_client,
    get_active_model,
    is_reasoning_model,
)


def test_openai_credentials_resolved(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-12345")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    api_key, base_url, provider = get_llm_credentials()
    assert api_key == "sk-test-openai-12345"
    assert provider == "openai"
    assert "openai.com" in base_url


def test_groq_credentials_resolved(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test-groq-12345")

    api_key, base_url, provider = get_llm_credentials()
    assert api_key == "gsk-test-groq-12345"
    assert provider == "groq"
    assert "groq.com" in base_url


def test_neither_key_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    # also mock ENV_PATH so it doesn't load from actual .env during test
    monkeypatch.setattr("generation.client.ENV_PATH", type("FakePath", (), {"exists": lambda s: False})())

    with pytest.raises(RuntimeError, match="Neither OPENAI_API_KEY nor GROQ_API_KEY"):
        get_llm_credentials()


def test_openai_model_dynamic_resolution(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    monkeypatch.delenv("RAG_GENERATION_MODEL", raising=False)

    model = get_active_model("RAG_GENERATION_MODEL")
    assert model == "gpt-5.4-mini"


def test_explicit_rag_model_overrides_openai_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("RAG_GENERATION_MODEL", "custom-model-test")

    model = get_active_model("RAG_GENERATION_MODEL")
    assert model == "custom-model-test"


def test_is_reasoning_model():
    assert is_reasoning_model("openai/gpt-oss-20b") is True
    assert is_reasoning_model("o1-mini") is True
    assert is_reasoning_model("o3-mini") is True
    assert is_reasoning_model("gpt-4o") is False
    assert is_reasoning_model("gpt-4o-mini") is False
    assert is_reasoning_model("gpt-5.4-mini") is False

