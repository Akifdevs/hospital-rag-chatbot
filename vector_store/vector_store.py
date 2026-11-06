"""MySQL-backed chunk and vector storage.

Embeddings are stored as compact float32 bytes in MySQL. Retrieval uses
NumPy cosine similarity after applying the document-version filter in SQL.
This keeps documents, chunks, metadata, and vectors in one database and
does not require a SQLite extension or a second vector service.
"""

import struct
import uuid
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import engine, get_session
from database.models import Chunk, Document, DocumentVersion


COLLECTION_NAME = "service_documents"
VECTOR_SIZE = 384
DISTANCE = "cosine"


class VectorSearchResult:
    """Drop-in result object exposing id, score, and payload."""

    def __init__(self, id: str, score: float, payload: Dict[str, Any]):
        self.id = id
        self.score = float(score)
        self.payload = payload

    def __repr__(self) -> str:
        return f"VectorSearchResult(id={self.id!r}, score={self.score:.4f}, payload={self.payload})"


def get_connection(db_path: Optional[Any] = None) -> Session:
    """Return a session connected to the configured MySQL database.

    ``db_path`` is retained for compatibility with older callers and ignored.
    """
    del db_path
    return get_session()


def get_thread_connection(db_path: Optional[Any] = None) -> Session:
    return get_connection(db_path)


def close_thread_connection() -> None:
    """Compatibility no-op; callers own and close their SQLAlchemy sessions."""


create_vector_client = get_connection
close_vector_client = close_thread_connection
close_vector_store = close_thread_connection


def init_vector_store(conn: Optional[Session] = None, db_path: Optional[Any] = None) -> None:
    """Create all relational and chunk tables in MySQL."""
    del db_path
    from database.connection import Base
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if conn is not None:
        conn.commit()


def create_collection(client: Optional[Any] = None, collection_name: str = COLLECTION_NAME) -> None:
    del client, collection_name
    init_vector_store()


def build_point_id(
    document_id: Optional[int],
    document_version_id: Optional[int],
    chunk_id: str,
) -> str:
    identifier = f"{document_id}:{document_version_id}:{chunk_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identifier))


def create_points(
    chunks: List[dict],
    document_id: Optional[int] = None,
    document_version_id: Optional[int] = None,
    version_number: Optional[int] = None,
) -> List[dict]:
    points = []
    for index, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        embedding = chunk.get("embedding")
        if embedding is None:
            raise ValueError(f"Chunk '{chunk_id}' is missing embedding.")
        if len(embedding) != VECTOR_SIZE:
            raise ValueError(
                f"Embedding length mismatch for chunk '{chunk_id}'. "
                f"Expected {VECTOR_SIZE}, got {len(embedding)}"
            )

        point_id = build_point_id(document_id, document_version_id, chunk_id)
        payload = {
            "document_id": document_id,
            "document_version_id": document_version_id,
            "version_number": version_number,
            "chunk_id": chunk_id,
            "document": chunk.get("document"),
            "heading": chunk.get("heading"),
            "heading_level": chunk.get("heading_level"),
            "heading_path": chunk.get("heading_path", []),
            "content": chunk.get("content", ""),
            "text": chunk.get("text", ""),
            "start_line": chunk.get("start_line"),
            "end_line": chunk.get("end_line"),
        }
        points.append({
            "id": point_id,
            "point_id": point_id,
            "vector": embedding,
            "embedding": embedding,
            "document_id": document_id,
            "document_version_id": document_version_id,
            "version_number": version_number,
            "chunk_id": chunk_id,
            "chunk_index": index,
            "text": chunk.get("text", ""),
            "content": chunk.get("content", ""),
            "payload": payload,
        })
    return points


def _ensure_parents(session: Session, point: dict) -> None:
    document_id = point.get("document_id")
    version_id = point.get("document_version_id")
    if document_id is None:
        return

    document = session.get(Document, document_id)
    if document is None:
        document = Document(
            id=document_id,
            document_number=str(document_id),
            name=str(document_id),
        )
        session.add(document)
        session.flush()

    if version_id is not None and session.get(DocumentVersion, version_id) is None:
        session.add(DocumentVersion(
            id=version_id,
            document_id=document_id,
            version_number=point.get("version_number") or 1,
            file_name="doc",
            storage_key="key",
            sha256="placeholder",
            status="ready",
        ))
        session.flush()


def insert_points(
    client: Optional[Any],
    points: List[dict],
    collection_name: str = COLLECTION_NAME,
) -> int:
    del collection_name
    if not points:
        raise ValueError("Cannot insert zero points.")

    session = client if isinstance(client, Session) else get_session()
    owns_session = session is not client
    try:
        for point in points:
            embedding = point.get("vector") or point.get("embedding")
            if embedding is None:
                raise ValueError("Embedding cannot be None.")
            if len(embedding) != VECTOR_SIZE:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {VECTOR_SIZE}, got {len(embedding)}"
                )

            _ensure_parents(session, point)
            point_id = point.get("id") or point.get("point_id")
            chunk = session.scalar(select(Chunk).where(Chunk.point_id == point_id))
            if chunk is None:
                chunk = Chunk(point_id=point_id)
                session.add(chunk)

            chunk.document_id = point.get("document_id")
            chunk.document_version_id = point.get("document_version_id")
            chunk.version_number = point.get("version_number") or 1
            chunk.chunk_id = point.get("chunk_id")
            chunk.chunk_index = point.get("chunk_index", 0)
            chunk.text = point.get("text", "")
            chunk.content = point.get("content", "")
            chunk.metadata_json = point.get("payload") or {}
            chunk.embedding = struct.pack(
                f"<{VECTOR_SIZE}f", *(float(value) for value in embedding)
            )

        session.commit()
        return len(points)
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def _payload(chunk: Chunk) -> Dict[str, Any]:
    payload = dict(chunk.metadata_json or {})
    payload.setdefault("document_id", chunk.document_id)
    payload.setdefault("document_version_id", chunk.document_version_id)
    payload.setdefault("version_number", chunk.version_number)
    payload.setdefault("chunk_id", chunk.chunk_id)
    payload.setdefault("text", chunk.text or "")
    payload.setdefault("content", chunk.content or "")
    return payload


def search(
    query_vector: List[float],
    document_version_ids: List[int],
    top_k: int = 3,
    min_score: float = 0.70,
    client: Optional[Any] = None,
    force_numpy: bool = False,
) -> List[VectorSearchResult]:
    del force_numpy
    if len(query_vector) != VECTOR_SIZE:
        raise ValueError(
            f"Query vector dimension mismatch: expected {VECTOR_SIZE}, got {len(query_vector)}"
        )
    if not document_version_ids:
        return []

    session = client if isinstance(client, Session) else get_session()
    owns_session = session is not client
    try:
        chunks = list(session.scalars(
            select(Chunk).where(Chunk.document_version_id.in_(document_version_ids))
        ).all())
        if not chunks:
            return []

        query = np.asarray(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm:
            query = query / query_norm

        matrix = np.asarray([
            struct.unpack(f"<{VECTOR_SIZE}f", chunk.embedding)
            for chunk in chunks
        ], dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        scores = np.dot(matrix / norms, query)
        ordered = np.argsort(scores)[::-1]

        results = []
        for index in ordered:
            score = float(scores[index])
            if score < min_score:
                continue
            chunk = chunks[index]
            results.append(VectorSearchResult(chunk.point_id, score, _payload(chunk)))
            if len(results) >= top_k:
                break
        return results
    finally:
        if owns_session:
            session.close()


def count_document_version(
    client: Optional[Any],
    document_version_id: int,
    collection_name: str = COLLECTION_NAME,
) -> int:
    del collection_name
    session = client if isinstance(client, Session) else get_session()
    owns_session = session is not client
    try:
        return len(session.scalars(
            select(Chunk.id).where(Chunk.document_version_id == document_version_id)
        ).all())
    finally:
        if owns_session:
            session.close()


def delete_document_version(
    client: Optional[Any],
    document_version_id: int,
    collection_name: str = COLLECTION_NAME,
) -> bool:
    del collection_name
    session = client if isinstance(client, Session) else get_session()
    owns_session = session is not client
    try:
        chunks = list(session.scalars(
            select(Chunk).where(Chunk.document_version_id == document_version_id)
        ).all())
        if not chunks:
            return False
        for chunk in chunks:
            session.delete(chunk)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def verify_collection(
    client: Optional[Any],
    expected_count: int,
    collection_name: str = COLLECTION_NAME,
) -> int:
    del collection_name
    session = client if isinstance(client, Session) else get_session()
    owns_session = session is not client
    try:
        actual_count = len(session.scalars(select(Chunk.id)).all())
    finally:
        if owns_session:
            session.close()

    if actual_count < expected_count:
        raise RuntimeError(
            "MySQL vector count is lower than expected. "
            f"Expected at least: {expected_count}; actual: {actual_count}"
        )
    return actual_count
