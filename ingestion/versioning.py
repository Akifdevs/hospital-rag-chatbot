"""
ingestion/versioning.py
=======================

Authoritative home for:

1. Document identity extraction.
2. Identity normalization.
3. Major/minor global version-label decisions.

IMPORTANT:
Global versions are created ONLY by explicit/manual ingestion.

The watcher and application startup must never call ingestion or create
global snapshots.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger("strict-rag-versioning")


# ============================================================
# DOCUMENT TITLE / IDENTITY
# ============================================================

def extract_document_title(file_path: Path) -> str:
    """
    Extract the logical document identity from the document.

    The first Markdown heading (# or ##) is used as the identity.

    If no heading exists, the filename stem is used.
    """
    try:
        text = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        logger.warning(
            "Could not read file for title extraction | file=%s | error=%s",
            file_path,
            exc,
        )
        return file_path.stem

    for line in text.splitlines():
        stripped = line.strip()

        match = re.match(
            r"^#{1,2}\s+(.+)$",
            stripped,
        )

        if match:
            title = match.group(1).strip()

            if title:
                return title

    logger.warning(
        "No Markdown heading found — using filename as identity | file=%s",
        file_path.name,
    )

    return file_path.stem


def normalize_title(title: str) -> str:
    """
    Normalize a logical document identity.

    Case and repeated whitespace do not affect identity.
    """
    return re.sub(
        r"\s+",
        " ",
        title.strip(),
    ).lower()


# ============================================================
# GLOBAL VERSION DECISION
# ============================================================

def decide_next_version_label(
    repo,
    incoming_identities: set[str],
) -> tuple[int, int, str]:
    """
    Decide the next global semantic version.

    Rules:

    No ready snapshot:
        -> 1

    Same logical document identity set:
        -> minor bump
           1   -> 1.1 -> 1.2
           2   -> 2.1 -> 2.2

    Different logical document identity set:
        -> major bump
           1.x -> 2
           2.x -> 3

    IMPORTANT:
    This function ONLY calculates the label.

    It does NOT create a snapshot.
    The caller must decide whether a snapshot is actually necessary.
    """

    all_snapshots = repo.list_snapshots(
        ready_only=False
    )

    ready_snapshots = [
        snapshot
        for snapshot in all_snapshots
        if snapshot.status == "ready"
    ]

    # --------------------------------------------------------
    # First ready snapshot
    # --------------------------------------------------------

    if not ready_snapshots:
        logger.info(
            "No ready snapshots found -> starting global version 1"
        )

        return 1, 0, "1"

    # --------------------------------------------------------
    # Latest ready snapshot
    # --------------------------------------------------------

    ready_snapshots.sort(
        key=lambda snapshot: (
            snapshot.major_version,
            snapshot.minor_version,
        ),
        reverse=True,
    )

    latest = ready_snapshots[0]

    latest_identities = repo.get_snapshot_identities(
        latest.id
    )

    latest_normalized = {
        normalize_title(identity)
        for identity in latest_identities
    }

    incoming_normalized = {
        normalize_title(identity)
        for identity in incoming_identities
    }

    # --------------------------------------------------------
    # Same document set -> minor
    # --------------------------------------------------------

    if latest_normalized == incoming_normalized:

        base_major = latest.major_version

        max_minor = max(
            (
                snapshot.minor_version
                for snapshot in ready_snapshots
                if snapshot.major_version == base_major
            ),
            default=0,
        )

        new_minor = max_minor + 1
        label = f"{base_major}.{new_minor}"

        logger.info(
            "Document identity set unchanged -> next minor version %s",
            label,
        )

        return (
            base_major,
            new_minor,
            label,
        )

    # --------------------------------------------------------
    # Document set changed -> major
    # --------------------------------------------------------

    added = incoming_normalized - latest_normalized
    removed = latest_normalized - incoming_normalized

    max_major = max(
        (
            snapshot.major_version
            for snapshot in ready_snapshots
        ),
        default=0,
    )

    new_major = max_major + 1
    label = str(new_major)

    logger.info(
        "Document identity set changed -> major version %s | added=%s | removed=%s",
        label,
        sorted(added),
        sorted(removed),
    )

    return (
        new_major,
        0,
        label,
    )