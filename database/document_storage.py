from abc import ABC, abstractmethod
from pathlib import Path


# ============================================================
# DOCUMENT STORAGE INTERFACE
# ============================================================

class DocumentStorage(ABC):
    """
    Abstract interface for document storage.

    The ingestion pipeline depends on this interface rather
    than directly depending on the local filesystem.

    Implementations can provide:

        - Local filesystem storage
        - S3-compatible object storage
        - Cloud object storage
        - Other storage backends
    """

    @abstractmethod
    def store(
        self,
        source_file: Path,
        document_id: int,
        version_number: int,
    ) -> Path:
        """
        Store a document and return its accessible path.
        """
        raise NotImplementedError

    @abstractmethod
    def get_storage_key(
        self,
        document_id: int,
        version_number: int,
        filename: str,
    ) -> str:
        """
        Return the logical storage key for a document.
        """
        raise NotImplementedError