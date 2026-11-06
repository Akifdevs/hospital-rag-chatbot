import shutil
from pathlib import Path

from database.storage_paths import (
    get_document_path,
    get_storage_key,
    ensure_version_directory,
)

from storage.document_storage import (
    DocumentStorage,
)


# ============================================================
# LOCAL DOCUMENT STORAGE
# ============================================================

class LocalDocumentStorage(
    DocumentStorage
):
    """
    Store documents on the local filesystem.

    Example:

        data/documents/
        └── 1/
            └── versions/
                └── 2/
                    └── service-order-rag.md
    """

    def store(
        self,
        source_file: Path,
        document_id: int,
        version_number: int,
    ) -> Path:
        """
        Copy the source document into the versioned
        local storage directory.
        """

        source_file = Path(
            source_file
        )

        if not source_file.exists():

            raise FileNotFoundError(
                "Source document does not exist:\n"
                f"{source_file}"
            )

        if source_file.is_dir():

            raise ValueError(
                "Source document must be a file."
            )

        import re
        match = re.match(r"^version\s+(\d+)$", source_file.parent.name, re.IGNORECASE)
        v_num = int(match.group(1)) if match else version_number

        # ----------------------------------------------------
        # Ensure destination directory exists.
        # ----------------------------------------------------

        ensure_version_directory(
            document_id,
            v_num,
        )

        # ----------------------------------------------------
        # Build destination path using the existing centralized
        # path validation.
        # ----------------------------------------------------

        destination = get_document_path(
            document_id,
            v_num,
            source_file.name,
        )

        # ----------------------------------------------------
        # Copy document if not already in place.
        # ----------------------------------------------------

        if source_file.resolve() != destination.resolve():
            shutil.copy2(
                source_file,
                destination,
            )

        return destination

    store_document = store

    def get_storage_key(
        self,
        document_id: int,
        version_number: int,
        filename: str,
    ) -> str:
        """
        Return the logical storage key for the document.
        """

        return get_storage_key(
            document_id,
            version_number,
            filename,
        )