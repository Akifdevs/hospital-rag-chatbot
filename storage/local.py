import re
import shutil
from pathlib import Path
from typing import BinaryIO

from storage.base import DocumentStorage


SEMANTIC_VERSION_PATTERN = re.compile(
    r"^version\s+(\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)


def normalize_version_label(
    version_number: str | int,
) -> str:
    """
    Convert an internal version argument into a semantic
    filesystem version label.

    Accepted:

        1
        "1"
        "1.1"
        "2.3"
    """

    label = str(
        version_number
    ).strip()

    if not re.match(
        r"^\d+(?:\.\d+)?$",
        label,
    ):
        raise ValueError(
            "Invalid semantic version label: "
            f"{version_number!r}"
        )

    if label.endswith(".0"):
        label = label[:-2]

    return label


class LocalDocumentStorage(
    DocumentStorage
):

    def __init__(
        self,
        base_directory: Path,
    ):
        self.base_directory = (
            base_directory.resolve()
        )

        self.base_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ========================================================
    # SAFE PATH RESOLUTION
    # ========================================================

    def _resolve(
        self,
        key: str,
    ) -> Path:

        path = (
            self.base_directory
            / key
        ).resolve()

        if not str(path).startswith(
            str(self.base_directory)
        ):
            raise ValueError(
                "Invalid storage key."
            )

        return path

    # ========================================================
    # GENERIC STORAGE API
    # ========================================================

    def save(
        self,
        key: str,
        file: BinaryIO,
    ) -> str:

        destination = self._resolve(
            key
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with destination.open(
            "wb"
        ) as output:

            while True:

                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                output.write(
                    chunk
                )

        return key

    def open(
        self,
        key: str,
    ) -> BinaryIO:

        path = self._resolve(
            key
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Document not found: {key}"
            )

        return path.open(
            "rb"
        )

    def exists(
        self,
        key: str,
    ) -> bool:

        return self._resolve(
            key
        ).exists()

    # ========================================================
    # DOCUMENT STORAGE
    # ========================================================

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

        # ----------------------------------------------------
        # If the source file is already inside a semantic
        # version folder, preserve that folder label.
        #
        # Examples:
        #
        #   version 1
        #   version 1.1
        #   version 2
        #   version 2.1
        # ----------------------------------------------------

        match = SEMANTIC_VERSION_PATTERN.match(
            source_file.parent.name
        )

        if match:
            version_label = normalize_version_label(
                match.group(1)
            )
        else:
            version_label = normalize_version_label(
                version_number
            )

        version_directory = (
            self.base_directory
            / f"version {version_label}"
        )

        version_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            version_directory
            / source_file.name
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

        version_label = normalize_version_label(
            version_number
        )

        return (
            f"version {version_label}/"
            f"{filename}"
        )