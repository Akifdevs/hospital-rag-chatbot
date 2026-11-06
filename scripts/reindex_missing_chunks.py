#!/usr/bin/env python3
"""Rebuild missing chunk embeddings in the MySQL database."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sentence_transformers import SentenceTransformer  # noqa: E402

from database.connection import get_session, init_database  # noqa: E402
from database.models import DocumentVersion  # noqa: E402
from ingestion.chunker import parse_markdown  # noqa: E402
from ingestion.embedder import MODEL_NAME, build_embedding_text  # noqa: E402
from vector_store.vector_store import (  # noqa: E402
    VECTOR_SIZE,
    count_document_version,
    create_points,
    insert_points,
)


def find_document_file(
    file_name: str,
    storage_key: str,
    expected_sha256: str,
    documents_dir: Path,
) -> Path | None:
    candidates = [
        documents_dir / storage_key,
        documents_dir / Path(storage_key).name,
        documents_dir / file_name,
    ]
    candidates.extend(documents_dir.rglob(file_name))

    for candidate in dict.fromkeys(candidates):
        if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == expected_sha256:
            return candidate
    return None


def reindex_version(session, model: SentenceTransformer, version: DocumentVersion, documents_dir: Path) -> int:
    current_count = count_document_version(session, version.id)
    if current_count >= version.chunk_count and version.chunk_count > 0:
        print(f"[SKIP] Version {version.id} already has {current_count} chunks in MySQL.")
        return current_count

    document_file = find_document_file(
        version.file_name,
        version.storage_key,
        version.sha256,
        documents_dir,
    )
    if document_file is None:
        raise FileNotFoundError(
            f"Could not find {version.file_name} for document version {version.id}"
        )

    _, chunks = parse_markdown(document_file)
    texts = [build_embedding_text(chunk) for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    if embeddings.shape[1] != VECTOR_SIZE:
        raise RuntimeError(
            f"Expected {VECTOR_SIZE}-dimensional embeddings, got {embeddings.shape[1]}"
        )

    embedded_chunks = []
    for chunk, text, embedding in zip(chunks, texts, embeddings):
        item = chunk.copy()
        item["text"] = text
        item["embedding"] = embedding.tolist()
        embedded_chunks.append(item)

    points = create_points(
        embedded_chunks,
        document_id=version.document_id,
        document_version_id=version.id,
        version_number=version.version_number,
    )
    insert_points(session, points)
    actual_count = count_document_version(session, version.id)
    print(f"[DONE] Version {version.id}: {actual_count} chunks in MySQL.")
    return actual_count


def main() -> None:
    init_database()
    documents_dir = BASE_DIR / "data" / "documents"
    session = get_session()
    try:
        versions = list(session.query(DocumentVersion).filter(
            DocumentVersion.status == "ready",
            DocumentVersion.chunk_count > 0,
        ).order_by(DocumentVersion.id))
        missing = [
            version for version in versions
            if count_document_version(session, version.id) < version.chunk_count
        ]
        print(f"Found {len(missing)} document version(s) needing reindexing.")
        if missing:
            model = SentenceTransformer(MODEL_NAME)
            for version in missing:
                reindex_version(session, model, version, documents_dir)
    finally:
        session.close()


if __name__ == "__main__":
    main()
