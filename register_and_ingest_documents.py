"""
register_and_ingest_documents.py
================================

Explicit/manual global document-set ingestion.

The global version is taken directly from the source folder name.

Examples:

    python register_and_ingest_documents.py "data/documents/version 1"
    python register_and_ingest_documents.py "data/documents/version 2"
    python register_and_ingest_documents.py "data/documents/version 3"

Version behavior:

    data/documents/version 1
        -> global snapshot "1"

    data/documents/version 2
        -> global snapshot "2"

    data/documents/version 3
        -> global snapshot "3"

There is NO automatic global version calculation.

There is NO comparison against the latest snapshot.

There is NO automatic 1.1 / 1.2 / 2.1 generation.

The per-document DocumentVersion.version_number system remains
unchanged and is handled by ingestion.sync.ingest_document().

Every successfully ingested global snapshot is immediately READY.

Application startup and the file watcher do not create versions.
Only explicitly running this command creates/updates a snapshot.
"""

import argparse
import hashlib
import logging
from pathlib import Path
import re
import uuid
from typing import Optional

from database.connection import (
    get_session,
    init_database,
)

from database.models import (
    Document,
    VersionSnapshot,
)

from database.repository import DocumentRepository

from ingestion.sync import ingest_document

from ingestion.versioning import (
    extract_document_title,
    normalize_title,
)


logger = logging.getLogger(
    "strict-rag-ingest"
)


# ============================================================
# HELPERS
# ============================================================


def calculate_file_sha256(
    file_path: Path,
) -> str:
    """
    Calculate SHA-256 for a source file.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(block)

    return sha256.hexdigest()


def extract_source_version(
    source_dir: Path,
) -> tuple[int, str]:
    """
    Extract the explicit global version from a folder named:

        version 1
        version 2
        version 3

    Returns:

        (major_version, version_label)

    Examples:

        version 1 -> (1, "1")
        version 2 -> (2, "2")
        version 10 -> (10, "10")

    Global versions are intentionally integer folder versions.
    """

    folder_name = source_dir.name.strip()

    match = re.fullmatch(
        r"version\s+(\d+)",
        folder_name,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Source folder must be named exactly like "
            "'version 1', 'version 2', 'version 3', etc. "
            f"Received: '{folder_name}'"
        )

    major_version = int(match.group(1))

    if major_version < 1:
        raise ValueError(
            "Global version must be >= 1. "
            f"Received: {major_version}"
        )

    return major_version, str(major_version)


def find_or_create_document(
    repository: DocumentRepository,
    title: str,
    file_path: Path,
) -> Document:
    """
    Resolve a source file to a logical Document.

    Matching is based primarily on the normalized document title.

    The per-document revision number is NOT managed here.
    """

    normalized = normalize_title(title)

    existing_docs = repository.list_documents()

    for document in existing_docs:

        if normalize_title(document.name) == normalized:
            return document

        # Backward compatibility with existing document_number values.
        if document.document_number.lower() in {
            normalized,
            file_path.stem.lower(),
        }:
            document.name = title
            repository.session.commit()
            return document

    # --------------------------------------------------------
    # Create a new logical document
    # --------------------------------------------------------

    slug = re.sub(
        r"[^a-zA-Z0-9_\-]+",
        "-",
        normalized,
    ).strip("-").upper()

    if not slug:
        slug = file_path.stem.upper()

    existing_by_number = repository.get_document_by_number(
        slug
    )

    if existing_by_number is not None:
        slug = (
            f"{slug}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

    document = repository.create_document(
        document_number=slug,
        name=title,
        description=f"Documentation for {title}",
    )

    logger.info(
        "Created logical document | id=%s | number=%s | name=%s",
        document.id,
        slug,
        title,
    )

    return document


def discover_candidate_files(
    source_dir: Path,
) -> list[Path]:
    """
    Discover source documents while ignoring temporary/hidden files.
    """

    files = [
        file
        for file in sorted(source_dir.glob("*"))
        if (
            file.is_file()
            and not file.name.startswith(
                (".", "~", "#")
            )
            and file.suffix.lower()
            in {
                ".md",
                ".txt",
                "",
            }
        )
    ]

    if files:
        return files

    # Fallback for other document extensions.
    return [
        file
        for file in sorted(source_dir.glob("*"))
        if (
            file.is_file()
            and not file.name.startswith(
                (".", "~", "#")
            )
        )
    ]


# ============================================================
# SUMMARY
# ============================================================


def _print_ingest_summary(
    snapshot: VersionSnapshot,
    ingested: list[dict],
) -> None:

    if not ingested:
        return

    col_name = max(
        len(row["name"])
        for row in ingested
    )

    col_file = max(
        len(row["file_name"])
        for row in ingested
    )

    col_name = max(
        col_name,
        len("Document"),
    )

    col_file = max(
        col_file,
        len("File"),
    )

    width = (
        col_name
        + col_file
        + 12
    )

    separator = "─" * width

    print()
    print("═" * width)

    print(
        f"  INGEST SUMMARY — Global Version "
        f"{snapshot.version_label} "
        f"[{snapshot.status}]"
    )

    print("═" * width)

    print(
        f"  {'Document':<{col_name}}  "
        f"{'File':<{col_file}}  "
        f"Chunks"
    )

    print(separator)

    total_chunks = 0

    for row in ingested:

        print(
            f"  {row['name']:<{col_name}}  "
            f"{row['file_name']:<{col_file}}  "
            f"{row['chunk_count']}"
        )

        total_chunks += row["chunk_count"]

    print(separator)

    print(
        f"  Total chunks: {total_chunks}"
    )

    print()

    print(
        f"  Version {snapshot.version_label} "
        f"is LIVE (status=ready)."
    )

    print(
        "  The RAG API can query it immediately."
    )

    print("═" * width)
    print()


# ============================================================
# MANUAL INGESTION
# ============================================================


def ingest_source_folder(
    source_dir: Path,
) -> Optional[VersionSnapshot]:
    """
    Explicitly ingest a document-set source directory.

    The global version is taken directly from the source folder.

    Example:

        data/documents/version 1
            -> global version "1"

        data/documents/version 2
            -> global version "2"

    This function does NOT:

        - compare against the latest snapshot
        - calculate a next global version
        - create minor versions
        - perform a no-op comparison

    The per-document DocumentVersion.version_number mechanism remains
    completely unchanged.
    """

    init_database()

    source_dir = Path(
        source_dir
    ).resolve()

    print("=" * 70)
    print("REGISTER + INGEST DOCUMENTS")
    print("=" * 70)

    print(
        f"\nSource folder:\n{source_dir}\n"
    )

    if (
        not source_dir.exists()
        or not source_dir.is_dir()
    ):
        raise FileNotFoundError(
            "Source directory does not exist "
            f"or is not a directory: {source_dir}"
        )

    # --------------------------------------------------------
    # Global version comes directly from the folder name.
    # --------------------------------------------------------

    major_version, version_label = extract_source_version(
        source_dir
    )

    print(
        f"Global version: {version_label}"
    )

    candidate_files = discover_candidate_files(
        source_dir
    )

    if not candidate_files:
        print(
            f"No document files found in: "
            f"{source_dir}"
        )
        return None

    session = get_session()

    repository = DocumentRepository(
        session
    )

    snapshot_documents: dict[int, int] = {}

    ingested_rows: list[dict] = []

    try:

        # ----------------------------------------------------
        # Resolve logical document identities first.
        # ----------------------------------------------------

        resolved_files: list[
            tuple[Path, str, Document]
        ] = []

        identity_to_file: dict[str, Path] = {}

        for source_file in candidate_files:

            title = extract_document_title(
                source_file
            )

            normalized_title = normalize_title(
                title
            )

            # ------------------------------------------------
            # Duplicate logical identities in one source set
            # are ambiguous.
            # ------------------------------------------------

            if normalized_title in identity_to_file:

                raise ValueError(
                    "Duplicate logical document identity "
                    f"'{title}' found in source folder. "
                    f"Files: "
                    f"{identity_to_file[normalized_title].name} "
                    f"and "
                    f"{source_file.name}"
                )

            identity_to_file[
                normalized_title
            ] = source_file

            document = find_or_create_document(
                repository,
                title,
                source_file,
            )

            resolved_files.append(
                (
                    source_file,
                    title,
                    document,
                )
            )

        # ----------------------------------------------------
        # Ingest every document in this explicit version folder.
        #
        # DocumentVersion.version_number is still managed by
        # ingest_document().
        # ----------------------------------------------------

        for (
            source_file,
            title,
            document,
        ) in resolved_files:

            print("-" * 70)

            print(
                f"Title: {title}"
            )

            print(
                f"File:  {source_file.name}"
            )

            print("-" * 70)

            print(
                f"Document ID: "
                f"{document.id} "
                f"({document.document_number})"
            )

            version = ingest_document(
                document_id=document.id,
                source_file=source_file,
            )

            snapshot_documents[
                document.id
            ] = version.id

            ingested_rows.append(
                {
                    "name": document.name,
                    "file_name": source_file.name,
                    "chunk_count": version.chunk_count,
                }
            )

            print(
                f"Result: v{version.version_number}, "
                f"status={version.status}, "
                f"chunks={version.chunk_count}\n"
            )

        # ----------------------------------------------------
        # ingest_document() uses its own database session.
        #
        # Commit/refresh this session before creating the
        # snapshot so the newly-created DocumentVersion rows
        # are visible here.
        # ----------------------------------------------------

        session.commit()

        # ----------------------------------------------------
        # Create the snapshot using the EXPLICIT folder version.
        #
        # There is deliberately no:
        #
        #   decide_next_version_label()
        #
        # and no comparison with another snapshot.
        # ----------------------------------------------------

        snapshot = repository.create_snapshot(
            document_versions=snapshot_documents,
            major_version=major_version,
            minor_version=0,
            version_label=version_label,
            status="ready",
        )

        logger.info(
            "Created ready global snapshot | version=%s",
            snapshot.version_label,
        )

        _print_ingest_summary(
            snapshot,
            ingested_rows,
        )

        return snapshot

    finally:
        session.close()


def main(
    source_dir: Path,
) -> Optional[VersionSnapshot]:
    """
    Compatibility entry point.
    """

    return ingest_source_folder(
        source_dir
    )


# ============================================================
# CLI
# ============================================================


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Explicitly ingest a document set. "
            "The global version is taken directly "
            "from the source folder name, e.g. "
            "'version 1', 'version 2', etc."
        )
    )

    parser.add_argument(
        "source_dir",
        type=Path,
        help=(
            "Directory containing the document files. "
            "The directory must be named 'version N'."
        ),
    )

    args = parser.parse_args()

    main(
        args.source_dir
    )