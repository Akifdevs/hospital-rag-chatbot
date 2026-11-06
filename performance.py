import logging
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# Load the .env file HERE, before any os.getenv() calls below run.
#
# Without this, whichever module happens to import `performance`
# first (directly or transitively) determines whether .env has
# already been loaded by config/settings.py or not. If `performance`
# is imported before that (e.g. via `rag_pipeline` -> `performance`,
# which happens before `database.connection` -> `config.settings` in
# api.py's import order), every constant below silently locks in its
# fallback default forever - editing .env afterwards has no effect
# until this is fixed. Loading it directly here makes this module
# self-sufficient regardless of import order.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.70"))
RAG_ENABLE_CACHE = env_bool("RAG_ENABLE_CACHE", True)
RAG_CACHE_TTL_SECONDS = float(os.getenv("RAG_CACHE_TTL_SECONDS", "300"))
RAG_CACHE_MAX_ENTRIES = int(os.getenv("RAG_CACHE_MAX_ENTRIES", "500"))
RAG_WARMUP_EMBEDDING_MODEL = env_bool("RAG_WARMUP_EMBEDDING_MODEL", True)
RAG_AUTO_INGEST = env_bool("RAG_AUTO_INGEST", False)
RAG_INGEST_WATCH_ROOT = os.getenv(
    "RAG_INGEST_WATCH_ROOT",
    "data/documents",
)
RAG_INGEST_SOURCE_SET_GLOB = os.getenv(
    "RAG_INGEST_SOURCE_SET_GLOB",
    "version *",
)
RAG_INGEST_WATCH_INTERVAL_SECONDS = float(
    os.getenv("RAG_INGEST_WATCH_INTERVAL_SECONDS", "2")
)
RAG_INGEST_DEBOUNCE_SECONDS = float(
    os.getenv("RAG_INGEST_DEBOUNCE_SECONDS", "1")
)
RAG_ENABLE_QUERY_REWRITE = env_bool("RAG_ENABLE_QUERY_REWRITE", True)
RAG_GENERATION_MAX_TOKENS = int(os.getenv("RAG_GENERATION_MAX_TOKENS", "1000"))
RAG_VERIFIER_MAX_TOKENS = int(os.getenv("RAG_VERIFIER_MAX_TOKENS", "2000"))
_DEFAULT_FALLBACK_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")
RAG_GENERATION_MODEL = os.getenv("RAG_GENERATION_MODEL", _DEFAULT_FALLBACK_MODEL)
RAG_VERIFIER_MODEL = os.getenv("RAG_VERIFIER_MODEL", _DEFAULT_FALLBACK_MODEL)
RAG_REWRITE_MODEL = os.getenv("RAG_REWRITE_MODEL", _DEFAULT_FALLBACK_MODEL)
RAG_DEFAULT_ROLE = os.getenv("RAG_DEFAULT_ROLE", "receptionist").strip().lower()
RAG_ROLE_CACHE_TTL_SECONDS = float(os.getenv("RAG_ROLE_CACHE_TTL_SECONDS", "60"))


@dataclass
class CacheEntry:
    value: Any
    created_at: float


class VersionedAnswerCache:
    def __init__(self, max_entries: int, ttl_seconds: float):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[tuple[str, str, str], CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _key(version: str, query: str, role: str = "") -> tuple[str, str, str]:
        return str(version), " ".join(query.lower().split()), str(role).strip().lower()

    def get(self, version: str, query: str, role: str = "") -> Optional[Any]:
        key = self._key(version, query, role)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if time.monotonic() - entry.created_at >= self.ttl_seconds:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return entry.value

    def set(self, version: str, query: str, value: Any, role: str = "") -> None:
        key = self._key(version, query, role)
        with self._lock:
            self._entries[key] = CacheEntry(value, time.monotonic())
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)


answer_cache = VersionedAnswerCache(
    max_entries=RAG_CACHE_MAX_ENTRIES,
    ttl_seconds=RAG_CACHE_TTL_SECONDS,
)


def timed(stage: str, started_at: float) -> None:
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logging.getLogger("strict-rag-performance").info(
        "stage=%s elapsed_ms=%.2f",
        stage,
        elapsed_ms,
    )
