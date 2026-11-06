from ingestion.manifest import (
    build_collection_name,
    get_document_version,
    get_next_index_version,
)


# ============================================================
# COLLECTION VERSIONING
# ============================================================

def test_collection_name():

    assert (
        build_collection_name(1)
        == "service_order_v1"
    )

    assert (
        build_collection_name(7)
        == "service_order_v7"
    )


# ============================================================
# INDEX VERSION
# ============================================================

def test_first_index_version():

    assert (
        get_next_index_version(None)
        == 1
    )


def test_next_index_version():

    manifest = {
        "index_version": 5
    }

    assert (
        get_next_index_version(
            manifest
        )
        == 6
    )


# ============================================================
# DOCUMENT VERSION
# ============================================================

def test_first_document_version():

    assert (
        get_document_version(
            None,
            "abc123"
        )
        == 1
    )


def test_unchanged_document_version():

    manifest = {

        "document_sha256":
            "abc123",

        "document_version":
            4
    }

    assert (
        get_document_version(
            manifest,
            "abc123"
        )
        == 4
    )


def test_changed_document_version():

    manifest = {

        "document_sha256":
            "abc123",

        "document_version":
            4
    }

    assert (
        get_document_version(
            manifest,
            "different-hash"
        )
        == 5
    )