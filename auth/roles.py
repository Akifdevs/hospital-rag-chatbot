import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from database.connection import get_session
from database.repository import DocumentRepository
from performance import (
    RAG_DEFAULT_ROLE,
    RAG_ROLE_CACHE_TTL_SECONDS,
)

ROLE_PATTERN = re.compile(r"^[a-z0-9_-]{1,50}$")
DENY_ALL_ROLE = "__deny_all__"


@dataclass
class CachedRole:
    name: str
    is_active: bool
    can_access_all: bool
    # list of (document_identifier, documentation_version)
    rules: List[tuple[str, Optional[str]]]


class RoleMemoryCache:
    def __init__(self, ttl_seconds: float):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[float, Optional[CachedRole]]] = {}
        self._lock = threading.Lock()

    def get(self, role_name: str) -> Optional[tuple[bool, Optional[CachedRole]]]:
        with self._lock:
            entry = self._cache.get(role_name)
            if entry is None:
                return None
            created_at, val = entry
            if time.monotonic() - created_at >= self.ttl_seconds:
                del self._cache[role_name]
                return None
            return (True, val)

    def set(self, role_name: str, val: Optional[CachedRole]) -> None:
        with self._lock:
            self._cache[role_name] = (time.monotonic(), val)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_role_cache = RoleMemoryCache(ttl_seconds=RAG_ROLE_CACHE_TTL_SECONDS)


def clear_role_cache() -> None:
    """Clear in-memory role cache (useful for tests or immediate reloads)."""
    _role_cache.clear()


def get_cached_role(role_name: str) -> Optional[CachedRole]:
    norm_name = role_name.strip().lower()
    hit = _role_cache.get(norm_name)
    if hit is not None:
        return hit[1]

    session = get_session()
    try:
        repo = DocumentRepository(session)
        db_role = repo.get_role(norm_name)
        if db_role is None:
            _role_cache.set(norm_name, None)
            return None

        cached = CachedRole(
            name=db_role.name,
            is_active=bool(db_role.is_active),
            can_access_all=bool(db_role.can_access_all),
            rules=[
                (
                    grant.document_identifier.lower(),
                    str(grant.documentation_version).strip()
                    if grant.documentation_version is not None
                    else None,
                )
                for grant in db_role.document_access
            ],
        )
        _role_cache.set(norm_name, cached)
        return cached
    finally:
        session.close()


def resolve_request_role(request: Any) -> str:
    # Client-declared role is NOT secure; replace with a verified token for real access control.
    raw_role: Optional[str] = None
    if hasattr(request, "role") and getattr(request, "role", None):
        raw_role = getattr(request, "role")
    elif hasattr(request, "headers") and request.headers is not None:
        raw_role = request.headers.get("X-User-Role")
    elif isinstance(request, dict):
        raw_role = request.get("role") or request.get("X-User-Role") or request.get("x-user-role")
    elif isinstance(request, str):
        raw_role = request

    candidate: Optional[str] = None
    if raw_role and isinstance(raw_role, str):
        cleaned = raw_role.strip().lower()
        if ROLE_PATTERN.fullmatch(cleaned):
            candidate = cleaned

    default_role = RAG_DEFAULT_ROLE.strip().lower()

    if candidate:
        role_info = get_cached_role(candidate)
        if role_info is not None and role_info.is_active:
            return role_info.name

    # Missing, invalid, unknown to DB, or inactive: fall back to default role
    default_info = get_cached_role(default_role)
    if default_info is not None and default_info.is_active:
        return default_info.name

    # If default role does not exist either, answer with normal generic refusal (deny all)
    return DENY_ALL_ROLE


def get_allowed_document_version_ids_for_role(
    role_name: str,
    snapshot: Any,
    documentation_version: Optional[Union[str, int]] = None,
) -> List[int]:
    if not role_name or role_name == DENY_ALL_ROLE:
        return []

    role_info = get_cached_role(role_name)
    if role_info is None or not role_info.is_active:
        return []

    snapshot_id = getattr(snapshot, "id", None)
    if snapshot_id is None:
        return []

    session = get_session()
    try:
        repo = DocumentRepository(session)
        doc_versions = repo.get_snapshot_document_versions(snapshot_id)
    finally:
        session.close()

    if role_info.can_access_all:
        return [vid for vid, _ in doc_versions]

    ver_str = (
        str(documentation_version).strip()
        if documentation_version is not None
        else None
    )
    allowed_stems = {
        doc_id
        for doc_id, rule_ver in role_info.rules
        if rule_ver is None or rule_ver == ver_str
    }

    return [
        vid
        for vid, stem in doc_versions
        if stem in allowed_stems
    ]


def get_role_allowed_documents_count(
    role_name: str,
    documentation_version: Optional[Union[str, int]] = None,
) -> int:
    if not role_name or role_name == DENY_ALL_ROLE:
        return 0

    role_info = get_cached_role(role_name)
    if role_info is None or not role_info.is_active:
        return 0

    if role_info.can_access_all:
        session = get_session()
        try:
            repo = DocumentRepository(session)
            return len(repo.list_all_document_identifiers())
        finally:
            session.close()

    ver_str = (
        str(documentation_version).strip()
        if documentation_version is not None
        else None
    )
    matching_stems = {
        doc_id
        for doc_id, rule_ver in role_info.rules
        if rule_ver is None or rule_ver == ver_str
    }
    return len(matching_stems)

