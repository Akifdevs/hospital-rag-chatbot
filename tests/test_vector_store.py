import os

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import Chunk, Document, DocumentVersion
from vector_store.vector_store import (
    VECTOR_SIZE,
    build_point_id,
    count_document_version,
    create_points,
    delete_document_version,
    insert_points,
    search,
)


MYSQL_TEST_DATABASE_URL = os.getenv("MYSQL_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MYSQL_TEST_DATABASE_URL,
    reason="Set MYSQL_TEST_DATABASE_URL to run MySQL vector integration tests",
)


@pytest.fixture
def db_session():
    test_engine = create_engine(MYSQL_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(test_engine)
    session = sessionmaker(bind=test_engine, autoflush=False)()
    yield session
    session.rollback()
    session.query(Chunk).delete()
    session.query(DocumentVersion).delete()
    session.query(Document).delete()
    session.commit()
    session.close()
    test_engine.dispose()


def make_chunks(prefix: str, count: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    vectors = rng.normal(size=(count, VECTOR_SIZE)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    return [
        {
            "chunk_id": f"{prefix}-{index}",
            "document": "test.md",
            "heading": f"Heading {index}",
            "heading_path": [f"Heading {index}"],
            "content": f"Content {index}",
            "text": f"Heading {index} Content {index}",
            "start_line": index * 10 + 1,
            "end_line": (index + 1) * 10,
            "embedding": vectors[index].tolist(),
        }
        for index in range(count)
    ]


def test_point_id_is_deterministic():
    point_id = build_point_id(1, 101, "chunk-1")
    assert point_id == build_point_id(1, 101, "chunk-1")


def test_insert_count_and_filtered_search(db_session):
    chunks = make_chunks("chunk", 8, seed=42)
    points = create_points(chunks, document_id=1, document_version_id=101, version_number=1)
    insert_points(db_session, points)

    assert count_document_version(db_session, 101) == 8
    results = search(
        chunks[0]["embedding"],
        document_version_ids=[101],
        top_k=3,
        min_score=0.0,
        client=db_session,
    )

    assert len(results) == 3
    assert results[0].payload["chunk_id"] == "chunk-0"
    assert all(result.payload["document_version_id"] == 101 for result in results)


def test_search_excludes_other_versions(db_session):
    version_one = make_chunks("v1", 3, seed=1)
    version_two = make_chunks("v2", 3, seed=2)
    insert_points(
        db_session,
        create_points(version_one, document_id=1, document_version_id=201, version_number=1)
        + create_points(version_two, document_id=1, document_version_id=202, version_number=2),
    )

    results = search(
        version_one[0]["embedding"],
        document_version_ids=[202],
        top_k=3,
        min_score=0.0,
        client=db_session,
    )
    assert results
    assert all(result.payload["document_version_id"] == 202 for result in results)


def test_delete_document_version(db_session):
    points = create_points(
        make_chunks("delete", 2, seed=3),
        document_id=2,
        document_version_id=303,
        version_number=1,
    )
    insert_points(db_session, points)

    assert delete_document_version(db_session, 303) is True
    assert count_document_version(db_session, 303) == 0
    assert delete_document_version(db_session, 303) is False
