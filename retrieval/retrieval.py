import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

from vector_store.vector_store import (
    COLLECTION_NAME,
    search as vector_search,
    close_vector_store,
)

from database.connection import get_session

from database.repository import (
    DocumentRepository,
)

from ingestion.embedder import (
    MODEL_NAME,
)

from sentence_transformers import SentenceTransformer

import threading
import time

from performance import (
    RAG_MIN_SCORE,
    RAG_TOP_K,
    timed,
)

try:
    from spellchecker import SpellChecker
except ImportError:  # pragma: no cover
    SpellChecker = None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

DEFAULT_TOP_K = RAG_TOP_K

DEFAULT_MIN_SCORE = RAG_MIN_SCORE

EMBEDDING_DIMENSION = int(
    os.getenv(
        "EMBEDDING_DIMENSION",
        "384",
    )
)


# ============================================================
# SPELL CORRECTION
# ============================================================
#
# Users often mistype words in their questions ("insurence",
# "lab reprot", "confrim order"). The embedding model is
# somewhat typo-tolerant, but small mistakes can still push
# the similarity score below RAG_MIN_SCORE and cause an
# unnecessary refusal. Correcting obvious typos before
# embedding makes the assistant noticeably more forgiving.
#
# Domain-specific / product words that a generic English
# dictionary would flag as "unknown" should be added here so
# they are never "corrected" into something else.

_spellchecker = SpellChecker() if SpellChecker is not None else None

if _spellchecker is not None:
    _spellchecker.word_frequency.load_words(
        [
                        "rag",
            "faq",
            "sku",
            "invoice",
            "checkout",
            "insurance",
            "reimbursement",
        ]
    )


def correct_query_spelling(query: str) -> str:
    """
    Best-effort correction of obviously misspelled words in the
    user's question, before it is embedded and used for
    retrieval.

    This intentionally only touches individual alphabetic words
    that the dictionary considers unknown, and only replaces
    them when a confident correction exists. It leaves numbers,
    punctuation, and already-correct words untouched, so it will
    not rewrite the user's intent - only fix likely typos.
    """

    if _spellchecker is None or not query:
        return query

    tokens = query.split(" ")
    corrected_tokens = []

    for token in tokens:
        # Separate any trailing punctuation so it is preserved.
        stripped = token.strip(".,!?;:()\"'")
        trailing = token[len(stripped):] if stripped else ""

        # Skip acronyms / currency codes written in capitals (AED, USD,
        # CPT, ...). The spell-checker was turning "AED" into "And".
        if (
            not stripped.isalpha()
            or len(stripped) < 3
            or stripped.isupper()
        ):
            corrected_tokens.append(token)
            continue

        lowered = stripped.lower()

        if lowered in _spellchecker:
            corrected_tokens.append(token)
            continue

        correction = _spellchecker.correction(lowered)

        if not correction or correction == lowered:
            corrected_tokens.append(token)
            continue

        # Preserve original capitalisation style.
        if stripped[0].isupper():
            correction = correction.capitalize()

        corrected_tokens.append(correction + trailing)

    return " ".join(corrected_tokens)


# ============================================================
# CLIENTS / EMBEDDING MODEL
# ============================================================

_embedding_model = None
_embedding_model_lock = threading.Lock()
def get_embedding_model():
    """Return the shared local query-embedding model.

    The model is loaded once per backend process and reused for
    subsequent chat requests. It is the same model used during
    document ingestion, so query/document vectors remain compatible.
    """

    global _embedding_model

    if _embedding_model is None:
        with _embedding_model_lock:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer(
                    MODEL_NAME
                )

    return _embedding_model


def close_vector_store():
    from vector_store.vector_store import close_vector_store as _cvs
    _cvs()



# ============================================================
# DOCUMENT VERSION VALIDATION
# ============================================================

def get_requested_snapshot(version: str):
    """
    Resolve and validate one complete global document snapshot.

    Retrieval is only allowed against a READY version.

    This prevents the chatbot from retrieving:

        - nonexistent snapshots
        - processing versions
        - failed versions

    Returns the DocumentVersion object.
    """

    started_at = time.perf_counter()
    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        snapshot = repository.get_snapshot(
            version,
            ready_only=True,
        )

        if snapshot is None:

            raise ValueError(
                "Requested global version is not ready or does not exist.\n"
                f"Version: {version}\n"
            )

        document_version_ids = (
            repository.get_snapshot_document_version_ids(
                snapshot.id
            )
        )

        if not document_version_ids:
            raise ValueError(
                "Requested global version contains no documents."
            )

        return snapshot, document_version_ids

    finally:

        session.close()
        timed("snapshot_lookup", started_at)


# ============================================================
# EMBEDDING
# ============================================================

# BAAI/bge-small-en-v1.5 is an ASYMMETRIC retrieval model: it was
# trained to embed queries and passages differently. BAAI's own
# usage instructions require prefixing QUERY text (never passage/
# chunk text) with this exact instruction before encoding, or
# retrieval quality measurably degrades. Ingestion embeds chunk
# text with no prefix (see ingestion/embedder.py) - that side must
# stay untouched; only queries get this prefix.
BGE_QUERY_INSTRUCTION = (
    "Represent this sentence for searching relevant passages: "
)


def generate_query_embedding(
    text: str,
):
    """
    Generate an embedding for the user's query.

    IMPORTANT:

    This embedding is generated for the query only.

    Document chunks are NOT embedded here.

    Document embeddings are created once during ingestion.
    """

    started_at = time.perf_counter()
    model = get_embedding_model()

    embedding = model.encode(
        BGE_QUERY_INSTRUCTION + text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embedding = embedding.tolist()

    # --------------------------------------------------------
    # Validate query embedding dimension.
    # --------------------------------------------------------

    if len(embedding) != EMBEDDING_DIMENSION:

        raise RuntimeError(

            "Query embedding dimension mismatch.\n"

            f"Expected: {EMBEDDING_DIMENSION}\n"

            f"Received: {len(embedding)}"
        )

    timed("embedding", started_at)
    return embedding


# ============================================================
# VERSION FILTER
# ============================================================

class SnapshotFilter(list):
    @property
    def must(self):
        class Condition:
            key = "document_version_id"
            class Match:
                def __init__(self, any_ids):
                    self.any = any_ids
            def __init__(self, any_ids):
                self.match = self.Match(any_ids)
        return [Condition(list(self))]


def build_snapshot_filter(
    document_version_ids: List[int],
) -> SnapshotFilter:
    """
    Build the filter list of document_version_ids for one complete global snapshot.
    """
    if not document_version_ids:
        raise ValueError(
            "document_version_ids must not be empty."
        )
    return SnapshotFilter(sorted(list(set(document_version_ids))))


# ============================================================
# CONTEXT BUILDER
# ============================================================

def build_context(
    results,
) -> str:
    """
    Convert retrieved MySQL vector results into the context
    provided to the generation stage.

    Version metadata is deliberately included in the context
    so the generator knows exactly which document/version
    the evidence came from.
    """

    context_parts = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        payload = result.payload or {}

        chunk_id = payload.get(
            "chunk_id"
        )

        document_id = payload.get(
            "document_id"
        )

        document_version_id = payload.get(
            "document_version_id"
        )

        version_number = payload.get(
            "version_number"
        )

        heading = payload.get(
            "heading",
            "",
        )

        heading_path = payload.get(
            "heading_path",
            [],
        )

        content = payload.get(
            "content",
            "",
        )

        context_parts.append(

            f"SOURCE {index}\n\n"

            f"Document ID:\n"
            f"{document_id}\n\n"

            f"Document Version ID:\n"
            f"{document_version_id}\n\n"

            f"Document Version:\n"
            f"{version_number}\n\n"

            f"Source Chunk ID:\n"
            f"{chunk_id}\n\n"

            f"Heading:\n"
            f"{heading}\n\n"

            f"Heading Path:\n"
            f"{' > '.join(heading_path)}\n\n"

            f"Content:\n"
            f"{content}"
        )

    return (
        "\n\n"
        + "\n\n".join(
            context_parts
        )
    )


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(
    query: str,
    version: str,
    snapshot_data=None,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve documentation chunks for ONE SPECIFIC
    document version.

    Parameters:

        query:
            User's natural-language question.

        version:
            Global snapshot version requested by the API.

        top_k:
            Maximum number of chunks to retrieve.

        min_score:
            Minimum similarity score.

    The retrieval process is:

        1. Validate requested global snapshot.
        2. Ensure every attached document revision is READY.
        4. Generate query embedding.
                5. Filter MySQL vectors by the snapshot's document revisions.
        6. Perform vector search.
        7. Apply relevance threshold.
        8. Build grounded context.

    Document chunks are never embedded here.
    """

    query = query.strip()

    # Fix likely typos before embedding, so minor spelling
    # mistakes don't push the query's similarity below
    # min_score and trigger an unnecessary refusal.
    query = correct_query_spelling(query)

    if not query:

        return {

            "query":
                query,

            "has_evidence":
                False,

            "results":
                [],

            "context":
                "",

            "collection_name":
                COLLECTION_NAME,

            "version":
                version,
        }

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if not re.fullmatch(r"[1-9]\d*(?:\.\d+)?", version):

        raise ValueError(
            "version must be a semantic global label such as '1' or '1.1'."
        )

    if top_k <= 0:

        raise ValueError(
            "top_k must be greater than zero."
        )

    if not 0.0 <= min_score <= 1.0:

        raise ValueError(
            "min_score must be between 0 and 1."
        )

    # ========================================================
    # VALIDATE DATABASE VERSION
    # ========================================================

    if snapshot_data is None:
        snapshot, document_version_ids = get_requested_snapshot(version)
    else:
        snapshot, document_version_ids = snapshot_data

    if role is not None:
        from auth.roles import get_allowed_document_version_ids_for_role
        document_version_ids = get_allowed_document_version_ids_for_role(
            role_name=role,
            snapshot=snapshot,
            documentation_version=version,
        )

    if not document_version_ids:
        return {
            "query": query,
            "has_evidence": False,
            "results": [],
            "context": "",
            "collection_name": COLLECTION_NAME,
            "version": version,
            "snapshot_id": getattr(snapshot, "id", None) if snapshot else None,
        }

    try:
        # ====================================================
        # QUERY EMBEDDING
        # ====================================================

        query_vector = (
            generate_query_embedding(
                query,
            )
        )

        # ====================================================
        # VERSION FILTER
        # ====================================================

        version_filter = (
            build_snapshot_filter(
                document_version_ids=document_version_ids,
            )
        )

        # ====================================================
        # VECTOR SEARCH
        # ====================================================

        search_started_at = time.perf_counter()
        results = vector_search(
            query_vector=query_vector,
            document_version_ids=version_filter,
            top_k=top_k,
            min_score=min_score,
        )
        logger.info(
    "VECTOR RESULTS | query=%r | version=%s | count=%d | scores=%s",
    query,
    version,
    len(results),
    [
        round(float(result.score), 4)
        for result in results
    ],
)
        timed("vector_search", search_started_at)

        # ====================================================
        # RELEVANCE GATE
        # ====================================================

        filtered_results = [

            result

            for result in results

            if result.score >= min_score
        ]

        if not filtered_results:

            return {

                "query":
                    query,

                "has_evidence":
                    False,

                "results":
                    [],

                "context":
                    "",

                "collection_name":
                    COLLECTION_NAME,

                "version":
                    version,

                "snapshot_id":
                    snapshot.id,
            }

        # ====================================================
        # DEFENSIVE VERSION VALIDATION
        # ====================================================

        # Even though MySQL filtered the version IDs above, validate the
        # returned payloads as an additional safety boundary.

        for result in filtered_results:

            payload = (
                result.payload or {}
            )

            returned_version_id = (
                payload.get(
                    "document_version_id"
                )
            )

            if returned_version_id not in document_version_ids:

                raise RuntimeError(

                    "Vector store returned a chunk "
                    "outside the requested global version."
                )

        # ====================================================
        # BUILD CONTEXT
        # ====================================================

        context = build_context(
            filtered_results
        )

        return {

            "query":
                query,

            "has_evidence":
                True,

            "results":
                filtered_results,

            "context":
                context,

            "collection_name":
                COLLECTION_NAME,

            "version":
                version,
        }

    finally:
        pass

def retrieve_many(
    queries: List[str],
    version: str,
    snapshot_data=None,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve evidence using multiple equivalent query phrasings.

    Every query is independently restricted to the exact same
    requested document snapshot.

    A chunk is eligible only if it reaches min_score for at least
    one query. Scores are merged using the strongest similarity
    observed for that chunk.
    """

    queries = [
        q.strip()
        for q in queries
        if isinstance(q, str) and q.strip()
    ]

    # Remove duplicates while preserving order.
    queries = list(dict.fromkeys(queries))

    if not queries:
        return {
            "query": "",
            "queries": [],
            "has_evidence": False,
            "results": [],
            "context": "",
            "collection_name": COLLECTION_NAME,
            "version": version,
        }

    # Resolve the snapshot ONCE.
    if snapshot_data is None:
        snapshot_data = get_requested_snapshot(version)

    snapshot, document_version_ids = snapshot_data
    if role is not None:
        from auth.roles import get_allowed_document_version_ids_for_role
        document_version_ids = get_allowed_document_version_ids_for_role(
            role_name=role,
            snapshot=snapshot,
            documentation_version=version,
        )
        snapshot_data = (snapshot, document_version_ids)

    if not document_version_ids:
        return {
            "query": queries[0],
            "queries": queries,
            "has_evidence": False,
            "results": [],
            "context": "",
            "collection_name": COLLECTION_NAME,
            "version": version,
        }

    merged = {}

    # Retrieve independently for every query.
    for query in queries:

        result = retrieve(
            query=query,
            version=version,
            snapshot_data=snapshot_data,
            top_k=top_k,
            min_score=min_score,
            role=role,
        )

        for item in result.get("results", []):

            chunk_key = item.id

            existing = merged.get(chunk_key)

            if existing is None:
                merged[chunk_key] = item
                continue

            # Keep the strongest semantic match.
            if item.score > existing.score:
                merged[chunk_key] = item

    if not merged:
        return {
            "query": queries[0],
            "queries": queries,
            "has_evidence": False,
            "results": [],
            "context": "",
            "collection_name": COLLECTION_NAME,
            "version": version,
        }

    # Strongest matches first.
    results = sorted(
        merged.values(),
        key=lambda item: float(item.score),
        reverse=True,
    )

    results = results[:top_k]

    logger.info(
        "FINAL CHUNKS | top_k=%s | %s",
        top_k,
        [
            (
                (item.payload or {}).get("chunk_id"),
                round(float(item.score), 4),
            )
            for item in results
        ],
    )

    # Defensive version validation AGAIN.
    _, document_version_ids = snapshot_data

    for result in results:

        payload = result.payload or {}

        returned_version_id = payload.get(
            "document_version_id"
        )

        if returned_version_id not in document_version_ids:
            raise RuntimeError(
                "Multi-query retrieval returned a chunk "
                "outside the requested global version."
            )

    context = build_context(results)

    return {
        "query": queries[0],
        "queries": queries,
        "has_evidence": bool(results),
        "results": results,
        "context": context,
        "collection_name": COLLECTION_NAME,
        "version": version,
    }



# ============================================================
# TERMINAL TEST
# ============================================================

def main():

    print("=" * 70)
    print("STRICT VERSION-AWARE RAG RETRIEVER")
    print("=" * 70)

    question = input(
        "\nEnter your question: "
    ).strip()

    version_input = input(
        "Enter global document-set version: "
    ).strip()

    if not version_input.isdigit():

        raise ValueError(
            "Document version must be an integer."
        )

    try:

        result = retrieve(

            query=question,

            version=int(
                version_input
            ),
        )

    except Exception as error:

        print()
        print(
            "Retrieval error:"
        )

        print(error)

        return

    # ========================================================
    # NO EVIDENCE
    # ========================================================

    if not result["has_evidence"]:

        print()
        print(
            "No sufficiently relevant documentation "
            "was found for the requested global version."
        )

        return

    # ========================================================
    # REQUESTED VERSION
    # ========================================================

    print()
    print(
        f"Global Version: "
        f"{result['version']}"
    )

    print(
        f"Collection: "
        f"{result['collection_name']}"
    )

    # ========================================================
    # RETRIEVAL RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("RETRIEVAL")
    print("=" * 70)

    for index, result_point in enumerate(
        result["results"],
        start=1,
    ):

        payload = (
            result_point.payload or {}
        )

        print()
        print(
            f"Result #{index}"
        )

        print(
            f"Score: "
            f"{result_point.score:.4f}"
        )

        print(
            "Document ID: "
            f"{payload.get('document_id')}"
        )

        print(
            "Version ID: "
            f"{payload.get('document_version_id')}"
        )

        print(
            "Version: "
            f"{payload.get('version_number')}"
        )

        print(
            "Chunk ID: "
            f"{payload.get('chunk_id')}"
        )

        print(
            "Heading: "
            f"{payload.get('heading')}"
        )

        print(
            "Path: "
            + " > ".join(
                payload.get(
                    "heading_path",
                    [],
                )
            )
        )

    print()
    print(
        "Evidence passed relevance gate."
    )

    print(
        f"Chunks passed: "
        f"{len(result['results'])}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()