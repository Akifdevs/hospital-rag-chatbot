from pathlib import Path
import re


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent
)


DOCUMENTS_ROOT = (
    BASE_DIR
    / "data"
    / "documents"
)


SEMANTIC_VERSION_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?$"
)


def normalize_version_label(
    version_number: str | int,
) -> str:
    """
    Normalize a global semantic version label.

    Accepted:

        1
        "1"
        1.1
        "1.1"

    Stored as a string because filesystem folder names are semantic
    global version labels.

    Examples:

        1       -> "1"
        "1"     -> "1"
        "1.1"   -> "1.1"
        2.3     -> "2.3"
    """

    label = str(
        version_number
    ).strip()

    if not SEMANTIC_VERSION_PATTERN.match(
        label
    ):
        raise ValueError(
            "Invalid version label. "
            "Expected 'N' or 'N.M'. "
            f"Received: {version_number!r}"
        )

    # Avoid storing "1.0" as a separate semantic version.
    if label.endswith(".0"):
        label = label[:-2]

    return label


def get_document_directory(
    document_id: int,
) -> Path:
    """
    Return the root document directory.

    document_id is retained for API compatibility.
    """

    return DOCUMENTS_ROOT


def get_version_directory(
    document_id: int,
    version_number: str | int,
) -> Path:

    version_label = normalize_version_label(
        version_number
    )

    return (
        DOCUMENTS_ROOT
        / f"version {version_label}"
    )


def get_document_path(
    document_id: int,
    version_number: str | int,
    filename: str,
) -> Path:

    filename_path = Path(
        filename
    )

    if (
        filename_path.name != filename
        or filename in {
            "",
            ".",
            "..",
        }
    ):
        raise ValueError(
            "Invalid document filename."
        )

    return (
        get_version_directory(
            document_id,
            version_number,
        )
        / filename
    )


def get_storage_key(
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


def ensure_version_directory(
    document_id: int,
    version_number: str | int,
) -> Path:

    directory = get_version_directory(
        document_id,
        version_number,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory