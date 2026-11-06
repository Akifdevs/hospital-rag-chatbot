import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_FILE = (
    BASE_DIR / "data" / "service-order-rag.md"
)

MANIFEST_FILE = (
    BASE_DIR / "data" / "document_manifest.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_COLLECTION_NAME = "service_order"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

EMBEDDING_DIMENSION = 384

# Number of successful index versions to retain.
INDEX_RETENTION = 3


# ============================================================
# HASHING
# ============================================================

def calculate_sha256(
    file_path: Path
) -> str:

    if not file_path.exists():

        raise FileNotFoundError(
            f"Document not found:\n{file_path}"
        )

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        for block in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):

            sha256.update(block)

    return sha256.hexdigest()


# ============================================================
# MANIFEST
# ============================================================

def load_manifest() -> Optional[Dict[str, Any]]:

    if not MANIFEST_FILE.exists():

        return None

    with MANIFEST_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_manifest(
    document: Path,
    document_hash: str,
    document_version: int,
    index_version: int,
    collection_name: str,
    chunk_count: int
) -> None:

    manifest = {

        "document":
            document.name,

        "document_sha256":
            document_hash,

        "document_version":
            document_version,

        "index_version":
            index_version,

        "collection_name":
            collection_name,

        "embedding_model":
            EMBEDDING_MODEL,

        "embedding_dimension":
            EMBEDDING_DIMENSION,

        "chunk_count":
            chunk_count,

        "status":
            "ready",

        "indexed_at":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = (
        MANIFEST_FILE.with_suffix(
            ".tmp"
        )
    )

    with temporary_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2
        )

    temporary_file.replace(
        MANIFEST_FILE
    )


# ============================================================
# VERSION HELPERS
# ============================================================

def get_next_index_version(
    previous_manifest: Optional[Dict[str, Any]]
) -> int:

    if not previous_manifest:

        return 1

    return (
        int(
            previous_manifest.get(
                "index_version",
                0
            )
        )
        + 1
    )


def get_document_version(
    previous_manifest: Optional[Dict[str, Any]],
    current_hash: str
) -> int:

    if not previous_manifest:

        return 1

    previous_hash = (
        previous_manifest.get(
            "document_sha256"
        )
    )

    previous_version = int(
        previous_manifest.get(
            "document_version",
            0
        )
    )

    if current_hash == previous_hash:

        return previous_version

    return previous_version + 1


# ============================================================
# COLLECTION NAME
# ============================================================

def build_collection_name(
    index_version: int
) -> str:

    return (
        f"{BASE_COLLECTION_NAME}_v"
        f"{index_version}"
    )


def get_active_collection_name() -> Optional[str]:

    manifest = load_manifest()

    if not manifest:

        return None

    if manifest.get("status") != "ready":

        return None

    return manifest.get(
        "collection_name"
    )


# ============================================================
# VERSION INFORMATION
# ============================================================

def get_active_version() -> Optional[int]:

    manifest = load_manifest()

    if not manifest:

        return None

    if manifest.get("status") != "ready":

        return None

    return int(
        manifest.get(
            "index_version",
            0
        )
    )


def get_retention_count() -> int:

    return INDEX_RETENTION