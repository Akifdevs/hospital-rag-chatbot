import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import Document, DocumentVersion
from database.repository import DocumentRepository


MYSQL_TEST_DATABASE_URL = os.getenv("MYSQL_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MYSQL_TEST_DATABASE_URL,
    reason="Set MYSQL_TEST_DATABASE_URL to run MySQL repository integration tests",
)


def test_get_latest_version_returns_newest_ready_version():
    engine = create_engine(MYSQL_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        document = Document(
            document_number="TEST-1",
            name="Test document",
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        session.add_all(
            [
                DocumentVersion(
                    document_id=document.id,
                    version_number=1,
                    file_name="v1.md",
                    storage_key="v1.md",
                    sha256="a",
                    status="ready",
                    is_latest=True,
                ),
                DocumentVersion(
                    document_id=document.id,
                    version_number=2,
                    file_name="v2.md",
                    storage_key="v2.md",
                    sha256="b",
                    status="processing",
                    is_latest=False,
                ),
                DocumentVersion(
                    document_id=document.id,
                    version_number=3,
                    file_name="v3.md",
                    storage_key="v3.md",
                    sha256="c",
                    status="failed",
                    is_latest=False,
                ),
                DocumentVersion(
                    document_id=document.id,
                    version_number=4,
                    file_name="v4.md",
                    storage_key="v4.md",
                    sha256="d",
                    status="ready",
                    is_latest=False,
                ),
            ]
        )
        session.commit()

        latest = DocumentRepository(session).get_latest_version(
            document.id
        )

        assert latest is not None
        assert latest.version_number == 4
        assert latest.status == "ready"


def test_global_snapshot_reuses_ready_document_versions():
    engine = create_engine(MYSQL_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        document_a = Document(
            document_number="A",
            name="Document A",
        )
        document_b = Document(
            document_number="B",
            name="Document B",
        )
        session.add_all([document_a, document_b])
        session.commit()
        session.refresh(document_a)
        session.refresh(document_b)

        version_a = DocumentVersion(
            document_id=document_a.id,
            version_number=1,
            file_name="a.md",
            storage_key="a.md",
            sha256="a",
            status="ready",
        )
        version_b = DocumentVersion(
            document_id=document_b.id,
            version_number=1,
            file_name="b.md",
            storage_key="b.md",
            sha256="b",
            status="ready",
        )
        session.add_all([version_a, version_b])
        session.commit()
        session.refresh(version_a)
        session.refresh(version_b)

        repository = DocumentRepository(session)
        snapshot_one = repository.create_snapshot(
            {
                document_a.id: version_a.id,
                document_b.id: version_b.id,
            }
        )
        snapshot_two = repository.create_snapshot(
            {
                document_a.id: version_a.id,
                document_b.id: version_b.id,
            }
        )

        assert snapshot_one.version_number == 1
        assert snapshot_two.version_number == 1
        assert snapshot_two.id == snapshot_one.id
        assert repository.get_snapshot(
            1,
            ready_only=True,
        ).id == snapshot_one.id
        assert repository.get_snapshot_document_version_ids(
            snapshot_two.id
        ) == [version_a.id, version_b.id]


def test_global_snapshot_creates_new_version_when_a_document_changes():
    engine = create_engine(MYSQL_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        document_a = Document(
            document_number="A-CHANGED",
            name="Document A",
        )
        document_b = Document(
            document_number="B-UNCHANGED",
            name="Document B",
        )
        session.add_all([document_a, document_b])
        session.commit()
        session.refresh(document_a)
        session.refresh(document_b)

        version_a_one = DocumentVersion(
            document_id=document_a.id,
            version_number=1,
            file_name="a-v1.md",
            storage_key="a-v1.md",
            sha256="a-v1",
            status="ready",
        )
        version_a_two = DocumentVersion(
            document_id=document_a.id,
            version_number=2,
            file_name="a-v2.md",
            storage_key="a-v2.md",
            sha256="a-v2",
            status="ready",
        )
        version_b_one = DocumentVersion(
            document_id=document_b.id,
            version_number=1,
            file_name="b-v1.md",
            storage_key="b-v1.md",
            sha256="b-v1",
            status="ready",
        )
        session.add_all([version_a_one, version_a_two, version_b_one])
        session.commit()
        session.refresh(version_a_one)
        session.refresh(version_a_two)
        session.refresh(version_b_one)

        repository = DocumentRepository(session)
        first = repository.create_snapshot(
            {
                document_a.id: version_a_one.id,
                document_b.id: version_b_one.id,
            }
        )
        second = repository.create_snapshot(
            {
                document_a.id: version_a_two.id,
                document_b.id: version_b_one.id,
            }
        )

        assert first.version_number == 1
        assert second.version_number == 2
        assert repository.get_snapshot_document_version_ids(
            second.id
        ) == [version_a_two.id, version_b_one.id]


def test_global_snapshot_rejects_incomplete_document_set():
    engine = create_engine(MYSQL_TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        document_a = Document(
            document_number="A-REQUIRED",
            name="Document A",
        )
        document_b = Document(
            document_number="B-REQUIRED",
            name="Document B",
        )
        session.add_all([document_a, document_b])
        session.commit()
        session.refresh(document_a)

        revision = DocumentVersion(
            document_id=document_a.id,
            version_number=1,
            file_name="a.md",
            storage_key="a.md",
            sha256="a",
            status="ready",
        )
        session.add(revision)
        session.commit()
        session.refresh(revision)

        try:
            DocumentRepository(session).create_snapshot(
                {document_a.id: revision.id}
            )
            assert False, "An incomplete snapshot should be rejected."
        except ValueError as error:
            assert "every registered document" in str(error)
