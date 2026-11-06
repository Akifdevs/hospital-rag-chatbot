import logging
import os
import threading
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger("strict-rag-llm")

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

_client_lock = threading.Lock()
_client_state = {
    "client": None,
    "api_key": None,
    "base_url": None,
    "provider": None,
}


def get_llm_credentials() -> Tuple[str, str, str]:
    """
    Dynamically resolve the active LLM provider, API key, and base URL.
    Checks environment variables on every call so changing keys or providers
    is picked up dynamically without hardcoding.

    Priority:
    1. OPENAI_API_KEY -> OpenAI (default base_url: https://api.openai.com/v1)
    2. GROQ_API_KEY   -> Groq   (default base_url: https://api.groq.com/openai/v1)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.strip():
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        return openai_key.strip(), base_url, "openai"

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        return groq_key.strip(), base_url, "groq"

    # If not found in current process env, attempt reloading from .env
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.strip():
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
            return openai_key.strip(), base_url, "openai"

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key.strip():
            base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
            return groq_key.strip(), base_url, "groq"

    raise RuntimeError(
        "Neither OPENAI_API_KEY nor GROQ_API_KEY is set in environment or .env."
    )


def create_llm_client() -> OpenAI:
    """
    Return an OpenAI client configured for the current API key and base URL.
    Re-creates the client automatically if the API key or provider changes.
    """
    global _client_state
    api_key, base_url, provider = get_llm_credentials()

    with _client_lock:
        if (
            _client_state["client"] is None
            or _client_state["api_key"] != api_key
            or _client_state["base_url"] != base_url
        ):
            logger.info("Initializing LLM client | provider=%s | base_url=%s", provider, base_url)
            _client_state["client"] = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            _client_state["api_key"] = api_key
            _client_state["base_url"] = base_url
            _client_state["provider"] = provider

        return _client_state["client"]


def get_active_model(var_name: str = "RAG_GENERATION_MODEL") -> str:
    """
    Dynamically resolve the model to use for generation, verification, or query rewriting.

    Priority:
    1. Specific env var (e.g. RAG_GENERATION_MODEL, RAG_VERIFIER_MODEL, RAG_REWRITE_MODEL)
    2. OPENAI_MODEL (e.g. gpt-5.4-mini)
    3. Provider default (openai/gpt-oss-20b for Groq, gpt-4o-mini for OpenAI)
    """
    explicit = os.getenv(var_name)
    openai_model = os.getenv("OPENAI_MODEL")

    if openai_model and openai_model.strip():
        if not explicit or explicit == "openai/gpt-oss-20b":
            return openai_model.strip()

    if explicit and explicit.strip():
        return explicit.strip()

    try:
        _, _, provider = get_llm_credentials()
    except Exception:
        provider = "openai"

    if provider == "groq":
        return "openai/gpt-oss-20b"
    return "gpt-4o-mini"


def is_reasoning_model(model_name: str) -> bool:
    """
    Check if the model accepts the 'reasoning_effort' parameter.
    Standard OpenAI models (gpt-4o, gpt-4o-mini, gpt-5.4-mini, etc.) reject reasoning_effort with HTTP 400.
    Only o1, o3, or Groq's gpt-oss models support it.
    """
    name = (model_name or "").lower()
    return name.startswith("o1") or name.startswith("o3") or "gpt-oss" in name


def get_token_param(token_count: int) -> dict:
    """
    Return appropriate token parameter dictionary:
    - 'max_completion_tokens' for OpenAI
    - 'max_tokens' for Groq
    """
    try:
        _, _, provider = get_llm_credentials()
    except Exception:
        provider = "openai"

    if provider == "openai":
        return {"max_completion_tokens": token_count}
    return {"max_tokens": token_count}


def chat_completion(client: OpenAI, **kwargs):
    """
    Execute chat completion with automatic fallback between
    'max_completion_tokens' (required by newer OpenAI models) and 'max_tokens' (legacy/Groq),
    as well as stripping unsupported parameters (like reasoning_effort or temperature) if rejected.
    """
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as e:
        err_msg = str(e).lower()
        retry_needed = False

        if "reasoning_effort" in kwargs and ("reasoning_effort" in err_msg or "unsupported parameter" in err_msg):
            kwargs.pop("reasoning_effort", None)
            retry_needed = True

        if "max_completion_tokens" in kwargs and ("unsupported" in err_msg or "max_completion_tokens" in err_msg or "max_tokens" in err_msg):
            kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
            retry_needed = True
        elif "max_tokens" in kwargs and ("max_completion_tokens" in err_msg or "unsupported" in err_msg):
            kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
            retry_needed = True

        if retry_needed:
            try:
                return client.chat.completions.create(**kwargs)
            except Exception as e2:
                err_msg2 = str(e2).lower()
                if "temperature" in kwargs and "temperature" in err_msg2:
                    kwargs.pop("temperature", None)
                    return client.chat.completions.create(**kwargs)
                raise e2
        raise
