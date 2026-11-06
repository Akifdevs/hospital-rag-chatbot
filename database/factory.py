from config.settings import (
    DOCUMENT_STORAGE_MODE,
)

from storage.document_storage import (
    DocumentStorage,
)

from storage.local_storage import (
    LocalDocumentStorage,
)


# ============================================================
# STORAGE FACTORY
# ============================================================

def create_document_storage() -> DocumentStorage:
    """
    Create the configured document storage backend.

    Currently supported:

        local

    Future implementations can be added here without changing
    the ingestion pipeline.
    """

    if (
        DOCUMENT_STORAGE_MODE
        == "local"
    ):

        return LocalDocumentStorage()

    raise RuntimeError(
        "Unsupported DOCUMENT_STORAGE_MODE: "
        f"{DOCUMENT_STORAGE_MODE}"
    )