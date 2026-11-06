"""
cleanup_stale_ingestion.py
==========================

Remove the old/stale ingestion state from the database.

IMPORTANT:
- Does NOT delete files from data/documents/
- Does NOT assume the existing Version 1 snapshot is correct
- Removes all existing global snapshots
- Removes all snapshot mappings
- Removes all document versions
- Removes all chunks/embeddings
- Removes all logical documents
- Leaves the source files untouched

Usage:

    python cleanup_stale_ingestion.py --dry-run

    python cleanup_stale_ingestion.py
"""

import argparse
import logging

from sqlalchemy import delete, select

from database.connection import get_session, init_database
from database.models import (
    Chunk,
    Document,
    DocumentVersion,
    SnapshotDocument,
    VersionSnapshot,
)

logger = logging.getLogger("stale-ingestion-cleanup")


def inspect_database(session):
    """Show what currently exists without modifying anything."""

    snapshots = list(
        session.scalars(
            select(VersionSnapshot).order_by(
                VersionSnapshot.version_number
            )
        ).all()
    )

    documents = list(
        session.scalars(
            select(Document).order_by(Document.id)
        ).all()
    )

    document_versions = list(
        session.scalars(
            select(DocumentVersion).order_by(
                DocumentVersion.id
            )
        ).all()
    )

    snapshot_documents = list(
        session.scalars(
            select(SnapshotDocument).order_by(
                SnapshotDocument.id
            )
        ).all()
    )

    chunks = list(
        session.scalars(
            select(Chunk).order_by(Chunk.id)
        ).all()
    )

    print()
    print("=" * 70)
    print("CURRENT DATABASE STATE")
    print("=" * 70)

    print(f"\nVersion snapshots:  {len(snapshots)}")
    for snapshot in snapshots:
        print(
            f"  id={snapshot.id} "
            f"version_label='{snapshot.version_label}' "
            f"legacy_version_number={snapshot.version_number} "
            f"status='{snapshot.status}'"
        )

    print(f"\nDocuments:          {len(documents)}")
    for document in documents:
        print(
            f"  id={document.id} "
            f"number='{document.document_number}' "
            f"name='{document.name}'"
        )

    print(f"\nDocument versions:  {len(document_versions)}")

    print(f"Snapshot mappings:  {len(snapshot_documents)}")

    print(f"Chunks/embeddings:  {len(chunks)}")

    print("=" * 70)
    print()


def cleanup_database(session, dry_run=False):
    """
    Remove all stale ingestion state.

    Deletion order is deliberate:

        chunks
          ↓
        snapshot mappings
          ↓
        document versions
          ↓
        snapshots
          ↓
        documents
    """

    snapshots = list(
        session.scalars(
            select(VersionSnapshot)
        ).all()
    )

    snapshot_documents = list(
        session.scalars(
            select(SnapshotDocument)
        ).all()
    )

    document_versions = list(
        session.scalars(
            select(DocumentVersion)
        ).all()
    )

    chunks = list(
        session.scalars(
            select(Chunk)
        ).all()
    )

    documents = list(
        session.scalars(
            select(Document)
        ).all()
    )

    print("=" * 70)
    print(
        "STALE INGESTION CLEANUP"
        + (" — DRY RUN" if dry_run else "")
    )
    print("=" * 70)

    print(
        f"\nSnapshots to remove:        {len(snapshots)}"
    )

    for snapshot in snapshots:
        print(
            f"  - version_label='{snapshot.version_label}' "
            f"(id={snapshot.id}, "
            f"legacy_number={snapshot.version_number})"
        )

    print(
        f"\nSnapshot mappings to remove: {len(snapshot_documents)}"
    )

    print(
        f"Document versions to remove: {len(document_versions)}"
    )

    for version in document_versions:
        print(
            f"  - id={version.id} "
            f"document_id={version.document_id} "
            f"version={version.version_number} "
            f"file='{version.file_name}'"
        )

    print(
        f"\nChunks/embeddings to remove: {len(chunks)}"
    )

    print(
        f"Logical documents to remove: {len(documents)}"
    )

    if dry_run:
        print()
        print("DRY RUN COMPLETE.")
        print("Nothing was deleted.")
        print("=" * 70)
        return

    # ----------------------------------------------------------
    # 1. Delete chunks / embeddings
    # ----------------------------------------------------------

    if chunks:
        for chunk in chunks:
            session.delete(chunk)

        session.flush()

    print(
        f"\n[DATABASE] Deleted {len(chunks)} chunks/embeddings."
    )

    # ----------------------------------------------------------
    # 2. Delete snapshot mappings
    # ----------------------------------------------------------

    if snapshot_documents:
        for mapping in snapshot_documents:
            session.delete(mapping)

        session.flush()

    print(
        "[DATABASE] Deleted "
        f"{len(snapshot_documents)} snapshot mappings."
    )

    # ----------------------------------------------------------
    # 3. Delete document versions
    # ----------------------------------------------------------

    if document_versions:
        for version in document_versions:
            session.delete(version)

        session.flush()

    print(
        "[DATABASE] Deleted "
        f"{len(document_versions)} document versions."
    )

    # ----------------------------------------------------------
    # 4. Delete global snapshots
    # ----------------------------------------------------------

    if snapshots:
        for snapshot in snapshots:
            session.delete(snapshot)

        session.flush()

    print(
        "[DATABASE] Deleted "
        f"{len(snapshots)} global snapshots."
    )

    # ----------------------------------------------------------
    # 5. Delete logical documents
    # ----------------------------------------------------------

    if documents:
        for document in documents:
            session.delete(document)

        session.flush()

    print(
        "[DATABASE] Deleted "
        f"{len(documents)} logical documents."
    )

    session.commit()

    print()
    print("=" * 70)
    print("DATABASE CLEANUP COMPLETE")
    print("=" * 70)


def verify_empty_database(session):
    """Verify that stale ingestion state is gone."""

    snapshot_count = session.scalar(
        select(VersionSnapshot.id)
    )

    document_count = session.scalar(
        select(Document.id)
    )

    document_version_count = session.scalar(
        select(DocumentVersion.id)
    )

    snapshot_document_count = session.scalar(
        select(SnapshotDocument.id)
    )

    chunk_count = session.scalar(
        select(Chunk.id)
    )

    print()
    print("=" * 70)
    print("POST-CLEANUP VERIFICATION")
    print("=" * 70)

    print(
        "Version snapshots: ",
        "EMPTY" if snapshot_count is None else "NOT EMPTY",
    )

    print(
        "Documents:         ",
        "EMPTY" if document_count is None else "NOT EMPTY",
    )

    print(
        "Document versions: ",
        "EMPTY"
        if document_version_count is None
        else "NOT EMPTY",
    )

    print(
        "Snapshot mappings: ",
        "EMPTY"
        if snapshot_document_count is None
        else "NOT EMPTY",
    )

    print(
        "Chunks/embeddings: ",
        "EMPTY"
        if chunk_count is None
        else "NOT EMPTY",
    )

    if any(
        value is not None
        for value in (
            snapshot_count,
            document_count,
            document_version_count,
            snapshot_document_count,
            chunk_count,
        )
    ):
        raise RuntimeError(
            "Cleanup verification failed. "
            "Some ingestion records still exist."
        )

    print()
    print("Database is clean.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Remove stale RAG ingestion data while "
            "leaving source documents untouched."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show what would be deleted without "
            "changing the database."
        ),
    )

    args = parser.parse_args()

    init_database()

    session = get_session()

    try:
        inspect_database(session)

        cleanup_database(
            session,
            dry_run=args.dry_run,
        )

        if not args.dry_run:
            verify_empty_database(session)

    finally:
        session.close()


if __name__ == "__main__":
    main()