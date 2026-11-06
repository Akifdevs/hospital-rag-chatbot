from config.settings import DOCUMENT_STORAGE_MODE
from storage.document_storage import DocumentStorage
from storage.local_storage import LocalDocumentStorage


def create_document_storage() -> DocumentStorage:
    """Create the configured document storage backend."""
    if DOCUMENT_STORAGE_MODE == "local":
        return LocalDocumentStorage()

    raise RuntimeError(
        "Unsupported DOCUMENT_STORAGE_MODE: "
        f"{DOCUMENT_STORAGE_MODE}"
    )


__all__ = ["DocumentStorage", "LocalDocumentStorage", "create_document_storage"]
