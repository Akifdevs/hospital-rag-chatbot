import hashlib
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer

from ingestion.chunker import parse_markdown

from ingestion.embedder import (
    build_embedding_text,
    MODEL_NAME,
)

from database.connection import get_session

from database.repository import (
    DocumentRepository,
)

from storage.factory import (
    create_document_storage,
)

from vector_store.vector_store import (
    COLLECTION_NAME,
    create_vector_client,
    create_points,
    insert_points,
    count_document_version,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

EMBEDDING_DIMENSION = 384


# ============================================================
# HASHING
# ============================================================

def calculate_sha256(
    file_path: Path,
) -> str:
    """
    Calculate the SHA-256 fingerprint of a document.

    The fingerprint is used to determine whether the exact
    same document content has already been ingested.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            f"Document not found:\n"
            f"{file_path}"
        )

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):

            sha256.update(block)

    return sha256.hexdigest()


# ============================================================
# CHUNK DOCUMENT
# ============================================================

def build_chunks(
    document_path: Path,
):
    """
    Parse a Markdown document into structured chunks.
    """

    print(
        "\n[1/4] Chunking document..."
    )

    headings, chunks = parse_markdown(
        document_path
    )

    if not chunks:

        raise RuntimeError(
            "Document produced zero chunks."
        )

    print(
        f"Detected headings: "
        f"{len(headings)}"
    )

    print(
        f"Created chunks: "
        f"{len(chunks)}"
    )

    return chunks


# ============================================================
# BUILD EMBEDDINGS
# ============================================================

def build_embeddings(
    chunks,
):
    """
    Generate embeddings for all document chunks.

    This function is called only during ingestion.

    It is never called by the query/retrieval path for
    document chunks.
    """

    print(
        "\n[2/4] Loading embedding model..."
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    texts = [
        build_embedding_text(
            chunk
        )
        for chunk in chunks
    ]

    if not texts:

        raise RuntimeError(
            "No texts available for embedding."
        )

    print(
        f"Generating {len(texts)} embeddings..."
    )

    embeddings = model.encode(

        texts,

        normalize_embeddings=True,

        show_progress_bar=True,
    )

    # --------------------------------------------------------
    # Validate count.
    # --------------------------------------------------------

    if len(embeddings) != len(chunks):

        raise RuntimeError(

            "Embedding count does not match "
            "chunk count.\n"

            f"Chunks: {len(chunks)}\n"

            f"Embeddings: {len(embeddings)}"
        )

    # --------------------------------------------------------
    # Validate dimension.
    # --------------------------------------------------------

    actual_dimension = (
        embeddings.shape[1]
    )

    if actual_dimension != (
        EMBEDDING_DIMENSION
    ):

        raise RuntimeError(

            "Embedding dimension mismatch.\n"

            f"Expected: "
            f"{EMBEDDING_DIMENSION}\n"

            f"Received: "
            f"{actual_dimension}"
        )

    embedded_chunks = []

    for (
        chunk,
        text,
        embedding,
    ) in zip(
        chunks,
        texts,
        embeddings,
    ):

        embedded_chunk = (
            chunk.copy()
        )

        embedded_chunk[
            "text"
        ] = text

        embedded_chunk[
            "embedding"
        ] = embedding.tolist()

        embedded_chunks.append(
            embedded_chunk
        )

    print(
        f"Generated "
        f"{len(embedded_chunks)} embeddings."
    )

    print(
        f"Embedding dimension: "
        f"{actual_dimension}"
    )

    return embedded_chunks


# ============================================================
# STORE DOCUMENT
# ============================================================

def store_document(
    source_file: Path,
    document_id: int,
    version_number: str | int,
):
    """
    Store the document using the configured storage backend.

    The ingestion pipeline does not directly depend on the
    local filesystem.

    The configured storage implementation determines where
    the document is physically stored.
    """

    storage = (
        create_document_storage()
    )

    return storage.store(

        source_file,

        document_id,

        version_number,
    )


# ============================================================
# GET STORAGE KEY
# ============================================================

def build_storage_key(
    document_id: int,
    version_number: str | int,
    filename: str,
):
    """
    Build the logical storage key using the configured
    storage backend.
    """

    storage = (
        create_document_storage()
    )

    return storage.get_storage_key(

        document_id,

        version_number,

        filename,
    )


# ============================================================
# BUILD VECTOR POINTS
# ============================================================

def build_vector_points(
    embedded_chunks,
    document_id: int,
    document_version_id: int,
    version_number: int,
):
    """
    Convert embedded chunks into vector store points.

    Every point receives document/version metadata.
    """

    return create_points(
        embedded_chunks,
        document_id=document_id,
        document_version_id=document_version_id,
        version_number=version_number,
    )


# Backward-compatible alias


# ============================================================
# INSERT VERSION
# ============================================================

def index_version(
    embedded_chunks,
    document_id: int,
    document_version_id: int,
    version_number: int,
):
    """
    Insert one document version into the shared vector store.
    """

    print(
        "\n[3/4] Indexing document version..."
    )

    client = create_vector_client()

    try:
        points = build_vector_points(
            embedded_chunks,
            document_id=document_id,
            document_version_id=document_version_id,
            version_number=version_number,
        )

        if not points:
            raise RuntimeError(
                "No vector points were generated."
            )

        print(
            f"Uploading {len(points)} vectors..."
        )

        insert_points(
            client,
            points,
            collection_name=COLLECTION_NAME,
        )

        return len(points)

    finally:
        client.close()


# ============================================================
# VERIFY VERSION
# ============================================================

def verify_version(
    document_version_id: int,
    expected_count: int,
):
    """
    Verify that the vector store contains the expected number of
    vectors for this specific document version.
    """

    print(
        "\n[4/4] Verifying indexed version..."
    )

    client = create_vector_client()

    actual_count = count_document_version(
        client,
        document_version_id,
        collection_name=COLLECTION_NAME,
    )

    if actual_count != expected_count:

        raise RuntimeError(

            "Vector store version verification "
            "failed.\n"

            f"Document version ID: "
            f"{document_version_id}\n"

            f"Expected: "
            f"{expected_count}\n"

            f"Actual: "
            f"{actual_count}"
        )

    print(
        "Vector store verification passed."
    )

    print(
        f"Stored vectors: "
        f"{actual_count}"
    )

    return actual_count


# ============================================================
# INGEST DOCUMENT
# ============================================================

def ingest_document(
    document_id: int,
    source_file: Path,
):
    """
    Ingest one document.

    The operation is idempotent.

    If the exact same content has already been successfully
    ingested, the function does nothing.

    If the content has changed, a new document version is
    created.
    """

    source_file = Path(
        source_file
    ).resolve()

    if not source_file.exists():

        raise FileNotFoundError(
            f"Source document does not exist:\n"
            f"{source_file}"
        )

    if source_file.is_dir():

        raise ValueError(
            "Source document must be a file."
        )

    # --------------------------------------------------------
    # Calculate document fingerprint.
    # --------------------------------------------------------

    document_hash = calculate_sha256(
        source_file
    )

    print("=" * 70)
    print("DOCUMENT INGESTION")
    print("=" * 70)

    print(
        f"\nDocument ID: "
        f"{document_id}"
    )

    print(
        f"Source file:\n"
        f"{source_file}"
    )

    print(
        f"\nSHA-256:\n"
        f"{document_hash}"
    )

    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        # ----------------------------------------------------
        # Make sure the document exists.
        # ----------------------------------------------------

        document = repository.get_document(
            document_id
        )

        if document is None:

            raise ValueError(

                "Document does not exist in "
                "the database.\n"

                f"Document ID: "
                f"{document_id}"
            )

        print(
            f"\nDocument:"
            f" {document.name}"
        )

        print(
            f"Document number:"
            f" {document.document_number}"
        )

        # ----------------------------------------------------
        # IDEMPOTENCY CHECK
        # ----------------------------------------------------

        existing_version = (
            repository.get_version_by_sha256(

                document_id,

                document_hash,
            )
        )

        if existing_version:

            print()
            print("=" * 70)
            print("DOCUMENT ALREADY INGESTED")
            print("=" * 70)

            print(
                f"\nVersion: "
                f"{existing_version.version_number}"
            )

            print(
                f"Status: "
                f"{existing_version.status}"
            )

            print(
                "\nSkipping chunking, embedding, "
                "and vector store insertion."
            )

            return existing_version

        # ----------------------------------------------------
        # CREATE NEW VERSION
        # ----------------------------------------------------

        version = repository.create_version(

            document_id=document_id,

            file_name=source_file.name,

            storage_key="pending",

            sha256=document_hash,

            status="processing",
        )

        print()

        print(
            f"Created document version: "
            f"v{version.version_number}"
        )

        # ----------------------------------------------------
        # Generate logical storage key.
        # ----------------------------------------------------

        match = re.match(r"^version\s+(\d+(?:\.\d+)?)$", source_file.parent.name, re.IGNORECASE)
        source_version_label = match.group(1) if match else str(version.version_number)

        storage_key = (
            build_storage_key(

                document_id,

                source_version_label,

                source_file.name,
            )
        )

        version.storage_key = (
            storage_key
        )

        session.commit()

        # ----------------------------------------------------
        # Store physical document using configured backend.
        # ----------------------------------------------------

        stored_file = store_document(

            source_file,

            document_id,

            source_version_label,
        )

        print(
            f"\nStored document:\n"
            f"{stored_file}"
        )

        # ----------------------------------------------------
        # Chunk.
        # ----------------------------------------------------

        chunks = build_chunks(
            stored_file
        )

        # ----------------------------------------------------
        # Embed.
        # ----------------------------------------------------

        embedded_chunks = (
            build_embeddings(
                chunks
            )
        )

        # ----------------------------------------------------
        # Index in vector store.
        # ----------------------------------------------------

        stored_count = index_version(

            embedded_chunks,

            document_id=document_id,

            document_version_id=(
                version.id
            ),

            version_number=(
                version.version_number
            ),
        )

        # ----------------------------------------------------
        # Verify this exact version.
        # ----------------------------------------------------

        verify_version(

            document_version_id=(
                version.id
            ),

            expected_count=stored_count,
        )

        # ----------------------------------------------------
        # Mark version READY.
        # ----------------------------------------------------

        repository.update_version_status(

            version_id=version.id,

            status="ready",

            chunk_count=stored_count,
        )

        # ----------------------------------------------------
        # Promote to LATEST.
        # ----------------------------------------------------

        repository.set_latest(

            document_id=document_id,

            version_number=(
                version.version_number
            ),
        )

        # ----------------------------------------------------
        # Refresh version.
        # ----------------------------------------------------

        version = repository.get_version(

            document_id,

            version.version_number,
        )

        print()
        print("=" * 70)
        print("DOCUMENT INGESTION COMPLETE")
        print("=" * 70)

        print(
            f"\nDocument: "
            f"{document.name}"
        )

        print(
            f"Document number: "
            f"{document.document_number}"
        )

        print(
            f"Version: "
            f"v{version.version_number}"
        )

        print(
            f"Version ID: "
            f"{version.id}"
        )

        print(
            f"Status: "
            f"{version.status}"
        )

        print(
            f"Latest: "
            f"{version.is_latest}"
        )

        print(
            f"Chunks: "
            f"{version.chunk_count}"
        )

        print(
            f"Storage key:\n"
            f"{version.storage_key}"
        )

        return version

    except Exception:

        # ----------------------------------------------------
        # If a version was created but ingestion failed,
        # leave it as processing for now.
        #
        # The chatbot will never use processing versions
        # because retrieval only uses READY versions.
        # ----------------------------------------------------

        session.rollback()

        raise

    finally:

        session.close()


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    print("=" * 70)
    print("DOCUMENT INGESTION")
    print("=" * 70)

    print()

    print(
        "This command ingests a specific document into "
        "the MySQL database, storage layer, and vector index."
    )

    document_id = input(
        "\nEnter document ID: "
    ).strip()

    if not document_id.isdigit():

        raise ValueError(
            "Document ID must be an integer."
        )

    source_file = input(
        "Enter document file path: "
    ).strip()

    if not source_file:

        raise ValueError(
            "Document file path cannot be empty."
        )

    ingest_document(

        document_id=int(
            document_id
        ),

        source_file=Path(
            source_file
        ),
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()