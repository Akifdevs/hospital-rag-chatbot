import os
from pathlib import Path

from storage.local import LocalDocumentStorage


BASE_DIR = (
    Path(__file__).resolve().parent.parent
)


STORAGE_BACKEND = os.getenv(
    "DOCUMENT_STORAGE_BACKEND",
    "local",
)


LOCAL_STORAGE_PATH = Path(
    os.getenv(
        "DOCUMENT_STORAGE_PATH",
        str(
            BASE_DIR
            / "data"
            / "documents"
        ),
    )
)


def create_document_storage():

    if STORAGE_BACKEND == "local":

        return LocalDocumentStorage(
            LOCAL_STORAGE_PATH
        )

    raise ValueError(
        "Unsupported document storage backend: "
        f"{STORAGE_BACKEND}"
    )
