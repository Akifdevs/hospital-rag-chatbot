from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class DocumentStorage(ABC):

    @abstractmethod
    def save(
        self,
        key: str,
        file: BinaryIO,
    ) -> str:
        """
        Store a document and return its storage key.
        """
        raise NotImplementedError

    @abstractmethod
    def open(
        self,
        key: str,
    ) -> BinaryIO:
        """
        Open a stored document.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a document exists.
        """
        raise NotImplementedError

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

    store_document = store

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
