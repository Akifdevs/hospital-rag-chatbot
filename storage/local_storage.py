import re
import shutil
from pathlib import Path

from database.storage_paths import (
    ensure_version_directory,
    get_document_path,
    get_storage_key,
)

from storage.local import (
    LocalDocumentStorage as _LocalDocumentStorage,
)


SEMANTIC_VERSION_PATTERN = re.compile(
    r"^version\s+(\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)


class LocalDocumentStorage(
    _LocalDocumentStorage
):
    """
    Compatibility wrapper for the legacy
    storage.local_storage import path.
    """

    def __init__(
        self,
        base_directory: Path | None = None,
    ):

        if base_directory is None:

            base_directory = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "documents"
            )

        super().__init__(
            base_directory
        )

    def store(
        self,
        source_file: Path,
        document_id: int,
        version_number: str | int,
    ) -> Path:

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

        match = (
            SEMANTIC_VERSION_PATTERN.match(
                source_file.parent.name
            )
        )

        if match:

            version_label = (
                match.group(1)
            )

        else:

            version_label = str(
                version_number
            ).strip()

        ensure_version_directory(
            document_id,
            version_label,
        )

        destination = get_document_path(
            document_id,
            version_label,
            source_file.name,
        )

        if (
            source_file.resolve()
            != destination.resolve()
        ):

            shutil.copy2(
                source_file,
                destination,
            )

        return destination

    store_document = store

    def get_storage_key(
        self,
        document_id: int,
        version_number: str | int,
        filename: str,
    ) -> str:

        return get_storage_key(
            document_id,
            version_number,
            filename,
        )


__all__ = [
    "LocalDocumentStorage",
]