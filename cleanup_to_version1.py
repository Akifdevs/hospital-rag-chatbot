"""
cleanup_to_version1.py

Idempotent cleanup script to remove all data tied to versions 2 through 11
so only version 1 remains across disk and the MySQL database.

Usage:
    python cleanup_to_version1.py
    python cleanup_to_version1.py --dry-run
"""

import argparse
import hashlib
import os
import re
import shutil
from pathlib import Path

# Setup base directories
BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_ROOT = BASE_DIR / "data" / "documents"
V1_CANONICAL_SOURCE = Path(r"C:\Users\DELL\Downloads\appointment-scheduling-rag.md")


def calculate_sha256(path: Path) -> str:
    """Compute SHA-256 fingerprint for a file."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def cleanup_disk(dry_run: bool = False) -> list[str]:
    """Delete all version N directories where N > 1."""
    deleted_folders = []
    if not DOCUMENTS_ROOT.exists():
        return deleted_folders

    for item in sorted(DOCUMENTS_ROOT.iterdir()):
        if not item.is_dir():
            continue
        match = re.match(r"^version\s+(\d+)$", item.name, re.IGNORECASE)
        if match:
            version_num = int(match.group(1))
            if version_num > 1:
                deleted_folders.append(item.name)
                if not dry_run:
                    shutil.rmtree(item)
                    print(f"[DISK] Deleted: {item}")
                else:
                    print(f"[DRY-RUN] Would delete folder: {item}")

    return deleted_folders


def cleanup_database(dry_run: bool = False):
    """
    Remove VersionSnapshot rows with version_number > 1,
    and remove DocumentVersion rows not referenced by VersionSnapshot 1.
    """
    from database.connection import get_session
    from database.models import (
        Document,
        DocumentVersion,
        SnapshotDocument,
        VersionSnapshot,
    )

    session = get_session()
    try:
        # 1. Locate Version 1 Snapshot
        v1_snapshot = (
            session.query(VersionSnapshot)
            .filter(VersionSnapshot.version_number == 1)
            .first()
        )
        if not v1_snapshot:
            raise RuntimeError("VersionSnapshot with version_number=1 not found in database!")

        v1_doc_ver_ids = {sd.document_version_id for sd in v1_snapshot.documents}
        print(f"[DATABASE] Version 1 snapshot references DocumentVersion IDs: {sorted(v1_doc_ver_ids)}")

        # 2. Find Snapshots > 1
        extra_snapshots = (
            session.query(VersionSnapshot)
            .filter(VersionSnapshot.version_number > 1)
            .all()
        )
        extra_snapshot_nums = [s.version_number for s in extra_snapshots]

        # 3. Find DocumentVersions not in Version 1
        all_doc_vers = session.query(DocumentVersion).all()
        unreferenced_doc_vers = [
            dv for dv in all_doc_vers if dv.id not in v1_doc_ver_ids
        ]
        unreferenced_ids = [dv.id for dv in unreferenced_doc_vers]

        if dry_run:
            print(f"[DRY-RUN] Would delete VersionSnapshots: {extra_snapshot_nums}")
            print(f"[DRY-RUN] Would delete DocumentVersion IDs: {unreferenced_ids}")
            return unreferenced_ids, v1_doc_ver_ids

        # Delete extra snapshots (cascades to SnapshotDocument join rows)
        for s in extra_snapshots:
            session.delete(s)

        # Delete unreferenced document versions
        for dv in unreferenced_doc_vers:
            session.delete(dv)

        # Ensure Version 1 versions are marked latest & ready
        for dv_id in v1_doc_ver_ids:
            dv = session.get(DocumentVersion, dv_id)
            if dv:
                dv.is_latest = True
                dv.status = "ready"

        session.commit()
        print(f"[DATABASE] Deleted VersionSnapshots: {extra_snapshot_nums}")
        print(f"[DATABASE] Deleted {len(unreferenced_ids)} DocumentVersion rows: {unreferenced_ids}")
        return unreferenced_ids, v1_doc_ver_ids
    finally:
        session.close()


def cleanup_vector_store(deleted_version_ids: list[int], dry_run: bool = False):
    """Delete all points belonging to deleted document_version_id values from the vector store."""
    if not deleted_version_ids:
        print("[VECTOR STORE] No document version IDs to purge from vector store.")
        return

    from vector_store.vector_store import (
        COLLECTION_NAME,
        create_vector_client,
        delete_document_version,
    )

    if dry_run:
        print(f"[DRY-RUN] Would delete vector points with document_version_id in: {deleted_version_ids}")
        return

    client = create_vector_client()
    for dv_id in deleted_version_ids:
        delete_document_version(client, dv_id, collection_name=COLLECTION_NAME)
    print(f"[VECTOR STORE] Successfully purged points for DocumentVersion IDs: {deleted_version_ids}")


def verify_and_heal_version1(dry_run: bool = False):
    """Ensure data/documents/version 1 contains pristine original content matching DB snapshot 1."""
    v1_dir = DOCUMENTS_ROOT / "version 1"
    if not v1_dir.exists():
        raise RuntimeError(f"Directory not found: {v1_dir}")

    # Document 3 (Appointment Scheduling) canonical hash for Version 1
    V1_APPT_HASH = "9859f4fdbea4cc441907c5a33528557a5a58c6c50b09c3b4031d194e962f43af"
    appt_file = v1_dir / "appointment-scheduling-rag.md"

    if appt_file.exists():
        current_hash = calculate_sha256(appt_file)
        if current_hash != V1_APPT_HASH:
            print(f"[INTEGRITY] version 1 appointment-scheduling-rag.md has drifted (hash {current_hash[:8]} != expected {V1_APPT_HASH[:8]})")
            if V1_CANONICAL_SOURCE.exists() and calculate_sha256(V1_CANONICAL_SOURCE) == V1_APPT_HASH:
                if not dry_run:
                    shutil.copy2(V1_CANONICAL_SOURCE, appt_file)
                    print(f"[RESTORE] Restored version 1 appointment-scheduling-rag.md back to canonical Version 1 text.")
                else:
                    print(f"[DRY-RUN] Would restore version 1 appointment-scheduling-rag.md from {V1_CANONICAL_SOURCE}")
            else:
                print(f"[WARNING] Canonical source file not found at {V1_CANONICAL_SOURCE}.")
        else:
            print(f"[INTEGRITY] version 1 appointment-scheduling-rag.md matches canonical Version 1 hash.")


def main():
    parser = argparse.ArgumentParser(description="Clean up all data for versions 2-11, keeping only version 1.")
    parser.add_argument("--dry-run", action="store_true", help="Preview deletions without modifying disk or MySQL.")
    args = parser.parse_args()

    mode_label = "DRY RUN PREVIEW" if args.dry_run else "EXECUTION"
    print("=" * 70)
    print(f"CLEANUP TO VERSION 1 ({mode_label})")
    print("=" * 70)

    # 1. Disk Cleanup
    print("\n--- Step 1: Cleaning Disk ---")
    deleted_folders = cleanup_disk(dry_run=args.dry_run)
    if not deleted_folders:
        print("[DISK] No extra version folders found on disk.")

    # 2. Database Cleanup
    print("\n--- Step 2: Cleaning Database ---")
    deleted_version_ids, v1_ids = cleanup_database(dry_run=args.dry_run)

    # 3. Vector Store Cleanup
    print("\n--- Step 3: Purging Vector Store Vectors ---")
    cleanup_vector_store(deleted_version_ids, dry_run=args.dry_run)

    # 4. Version 1 Integrity
    print("\n--- Step 4: Verifying Version 1 Integrity ---")
    verify_and_heal_version1(dry_run=args.dry_run)

    print("\n" + "=" * 70)
    print(f"CLEANUP COMPLETED ({mode_label})")
    print("=" * 70)


if __name__ == "__main__":
    main()
