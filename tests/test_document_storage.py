from database.storage_paths import (
    get_document_path,
)

from storage.factory import (
    create_document_storage,
)

from storage.local_storage import (
    LocalDocumentStorage,
)

import pytest


# ============================================================
# LOCAL STORAGE
# ============================================================

def test_local_storage_is_created():

    storage = (
        LocalDocumentStorage()
    )

    assert storage is not None


def test_storage_factory_returns_local_storage(
    monkeypatch,
):

    monkeypatch.setattr(
        "storage.factory.DOCUMENT_STORAGE_MODE",
        "local",
    )

    storage = (
        create_document_storage()
    )

    assert isinstance(
        storage,
        LocalDocumentStorage,
    )


# ============================================================
# STORAGE KEY
# ============================================================

def test_local_storage_builds_storage_key():

    storage = (
        LocalDocumentStorage()
    )

    key = storage.get_storage_key(

        document_id=1,

        version_number=2,

        filename="service-order-rag.md",
    )

    assert key == (
        "version 2/service-order-rag.md"
    )


# ============================================================
# DOCUMENT PATH
# ============================================================

def test_document_path_is_versioned():

    path = get_document_path(

        document_id=1,

        version_number=2,

        filename="service-order-rag.md",
    )

    assert path.name == (
        "service-order-rag.md"
    )

    assert (
        path.parent.name
        == "version 2"
    )

    assert (
        path.parent.parent.name
        == "documents"
    )


# ============================================================
# STORE DOCUMENT
# ============================================================

def test_local_storage_copies_document(
    tmp_path,
    monkeypatch,
):

    source_file = (
        tmp_path
        / "example.md"
    )

    source_content = (
        "# Test Document\n\n"
        "This is test content."
    )

    source_file.write_text(
        source_content,
        encoding="utf-8",
    )

    import storage.local_storage as local_storage

    destination = (
        tmp_path
        / "documents"
        / "version 2"
        / "example.md"
    )

    # --------------------------------------------------------
    # Replace the real project storage path with a temporary
    # test location.
    # --------------------------------------------------------

    monkeypatch.setattr(

        local_storage,

        "get_document_path",

        lambda document_id,
               version_number,
               filename:

            destination,
    )

    # --------------------------------------------------------
    # Replace directory creation with temporary directory
    # creation.
    # --------------------------------------------------------

    monkeypatch.setattr(

        local_storage,

        "ensure_version_directory",

        lambda document_id,
               version_number:

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            ),
    )

    # --------------------------------------------------------
    # Create storage backend.
    # --------------------------------------------------------

    storage = (
        LocalDocumentStorage()
    )

    # --------------------------------------------------------
    # Store document.
    # --------------------------------------------------------

    stored_file = storage.store(

        source_file,

        document_id=1,

        version_number=2,
    )

    # --------------------------------------------------------
    # Verify file exists.
    # --------------------------------------------------------

    assert stored_file.exists()

    # --------------------------------------------------------
    # Verify content was preserved.
    # --------------------------------------------------------

    assert stored_file.read_text(
        encoding="utf-8"
    ) == source_content

    # --------------------------------------------------------
    # Verify filename.
    # --------------------------------------------------------

    assert stored_file.name == (
        "example.md"
    )


# ============================================================
# MISSING SOURCE
# ============================================================

def test_local_storage_rejects_missing_source(
    tmp_path,
):

    storage = (
        LocalDocumentStorage()
    )

    missing_file = (
        tmp_path
        / "missing.md"
    )

    with pytest.raises(
        FileNotFoundError
    ):

        storage.store(

            missing_file,

            document_id=1,

            version_number=1,
        )


# ============================================================
# DIRECTORY SOURCE
# ============================================================

def test_local_storage_rejects_directory(
    tmp_path,
):

    storage = (
        LocalDocumentStorage()
    )

    source_directory = (
        tmp_path
        / "documents"
    )

    source_directory.mkdir()

    with pytest.raises(
        ValueError,
        match="must be a file",
    ):

        storage.store(

            source_directory,

            document_id=1,

            version_number=1,
        )


# ============================================================
# INVALID FILENAME
# ============================================================

def test_invalid_filename_is_rejected():

    with pytest.raises(
        ValueError,
        match="Invalid document filename",
    ):

        get_document_path(

            document_id=1,

            version_number=1,

            filename="../secret.md",
        )


def test_empty_filename_is_rejected():

    with pytest.raises(
        ValueError,
        match="Invalid document filename",
    ):

        get_document_path(

            document_id=1,

            version_number=1,

            filename="",
        )


# ============================================================
# STORAGE FACTORY
# ============================================================

def test_storage_factory_rejects_unknown_mode(
    monkeypatch,
):

    monkeypatch.setattr(
        "storage.factory.DOCUMENT_STORAGE_MODE",
        "unknown",
    )

    with pytest.raises(
        RuntimeError,
        match="Unsupported DOCUMENT_STORAGE_MODE",
    ):

        create_document_storage()