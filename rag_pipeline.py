import logging
import re
import time
from typing import Any, Dict, List, Optional

from performance import (
    RAG_ENABLE_QUERY_REWRITE,
    timed,
)


# ============================================================
# CONFIGURATION
# ============================================================

REFUSAL_MESSAGE = (
    "I couldn't find information about that in the documentation. "
    "Could you try rephrasing your question, or ask about "
    "something else I can help with?"
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# RESULT BUILDERS
# ============================================================

def success_result(
    answer: str,
    sources: List[Dict[str, Any]],
) -> Dict[str, Any]:

    return {
        "success": True,
        "answer": answer,
        "sources": sources,
    }


def failure_result(
    stage: str,
    reason: str = "",
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a fail-closed RAG response.

    Internal diagnostic information is retained under
    "_error" for logging/development purposes and should
    never be exposed directly to API clients.
    """

    # The user never needs to know which documentation version was
    # searched, so the message is the same with or without `version`.
    answer = REFUSAL_MESSAGE

    result = {
        "success": False,
        "answer": answer,
        "sources": [],
    }

    if reason:

        result["_error"] = {
            "stage": stage,
            "reason": reason,
        }

    return result


# ============================================================
# SOURCE EXTRACTION
# ============================================================

def build_sources(
    retrieval_result,
) -> List[Dict[str, Any]]:
    """
    Convert retrieval results into safe public source
    metadata.

    Document/version information is included so the caller
    knows exactly where the evidence came from.
    """

    sources = []

    for result in retrieval_result.get(
        "results",
        [],
    ):

        payload = result.payload or {}

        sources.append({

            "document_id":
                payload.get(
                    "document_id"
                ),

            "document_version_id":
                payload.get(
                    "document_version_id"
                ),

            "version_number":
                payload.get(
                    "version_number"
                ),

            "chunk_id":
                payload.get(
                    "chunk_id"
                ),

            "document":
                payload.get(
                    "document"
                ),

            "heading":
                payload.get(
                    "heading"
                ),

            "heading_path":
                payload.get(
                    "heading_path",
                    [],
                ),

            "relevance":
                round(
                    float(
                        result.score
                    ),
                    4,
                ),

            "start_line":
                payload.get(
                    "start_line"
                ),

            "end_line":
                payload.get(
                    "end_line"
                ),
        })

    return sources


# ============================================================
# CONTEXT SOURCE IDs
# ============================================================

def extract_context_source_ids(
    context: str,
) -> set:
    """
    Extract actual chunk IDs from retrieved context.

    The generator/verifier must reference these IDs rather
    than arbitrary labels such as SOURCE 1 or SOURCE 2.
    """

    source_ids = set()

    lines = context.splitlines()

    for index, line in enumerate(
        lines
    ):

        if line.strip() == "Source Chunk ID:":

            if index + 1 < len(lines):

                source_id = (
                    lines[index + 1]
                    .strip()
                )

                if source_id:

                    source_ids.add(
                        source_id
                    )

    return source_ids


# ============================================================
# GENERATED CLAIM VALIDATION
# ============================================================

def validate_generated_claims(
    claims,
    context,
):
    """
    Validate that every generated claim points to a chunk
    that actually exists in the retrieved context.
    """

    valid_source_ids = (
        extract_context_source_ids(
            context
        )
    )

    if not valid_source_ids:

        raise ValueError(
            "Retrieved context contains no "
            "valid source chunk IDs."
        )

    if not claims:

        raise ValueError(
            "Generated answer contains no claims."
        )

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        if not isinstance(
            claim,
            dict,
        ):

            raise ValueError(
                f"Claim #{index} is not an object."
            )

        claim_text = claim.get(
            "text"
        )

        source_id = claim.get(
            "source_chunk_id"
        )

        if not claim_text:

            raise ValueError(
                f"Claim #{index} has no text."
            )

        if not source_id:

            raise ValueError(
                f"Claim #{index} has no source_chunk_id."
            )

        source_id = source_id.strip()

        # ----------------------------------------------------
        # Never allow SOURCE 1 / SOURCE 2 / etc.
        # ----------------------------------------------------

        if source_id.upper().startswith(
            "SOURCE "
        ):

            raise ValueError(
                f"Claim #{index} uses invalid "
                f"source ID: {source_id}"
            )

        # ----------------------------------------------------
        # Source must exist in retrieved context.
        # ----------------------------------------------------

        if source_id not in valid_source_ids:

            raise ValueError(

                f"Claim #{index} references a source "
                f"that was not retrieved: {source_id}"
            )

    return True


# ============================================================
# VERIFIER RESULT VALIDATION
# ============================================================

def validate_verification_result(
    verification,
    context,
):
    """
    Validate the verifier response.

    The verifier must:

        1. Return a boolean verified field.
        2. Return claims when verified.
        3. Mark every claim as supported.
        4. Reference real retrieved chunk IDs.
    """

    if not isinstance(
        verification,
        dict,
    ):

        raise ValueError(
            "Verifier returned an invalid result."
        )

    if not isinstance(
        verification.get(
            "verified"
        ),
        bool,
    ):

        raise ValueError(
            "Verifier result does not contain "
            "a valid 'verified' field."
        )

    if not verification.get(
        "verified"
    ):

        return False

    claims = verification.get(
        "claims",
        [],
    )

    if not claims:

        raise ValueError(
            "Verifier marked the answer verified "
            "but returned no claims."
        )

    valid_source_ids = (
        extract_context_source_ids(
            context
        )
    )

    for index, claim in enumerate(
        claims,
        start=1,
    ):

        if not isinstance(
            claim,
            dict,
        ):

            raise ValueError(
                f"Verifier claim #{index} "
                "is not an object."
            )

        if not claim.get(
            "supported",
            False,
        ):

            return False

        source_id = (
            claim.get(
                "source_chunk_id",
                "",
            )
            .strip()
        )

        if not source_id:

            raise ValueError(

                f"Verifier claim #{index} "
                "has no source ID."
            )

        if source_id not in valid_source_ids:

            raise ValueError(

                f"Verifier claim #{index} "
                f"references unknown source: "
                f"{source_id}"
            )

    return True


# ============================================================
# MAIN RAG FUNCTION
# ============================================================

def answer_question(
    query: str,
    version: str,
    snapshot_data=None,
    history: Optional[list] = None,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the complete strict RAG pipeline for ONE global
    document snapshot.

    Pipeline:

        User Question
              |
              v
        Version Validation
              |
              v
        Query Embedding
              |
              v
        Version-Filtered Retrieval
              |
              v
        Relevance Gate
              |
              v
        Generation
              |
              v
        Source Validation
              |
              v
        Claim Verification
              |
              v
        Final Fail-Closed Check
              |
              v
        Answer + Sources

    IMPORTANT:

    Document chunks are NOT embedded here.

    Their embeddings were created during ingestion and are
    already stored in MySQL.

    Only the user's query is embedded during retrieval.
    """

    question = query.strip()
    version = str(version).strip()

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not question:

        return failure_result(
            stage="input",
            reason="Question is empty.",
        )

    if not re.fullmatch(r"[1-9]\d*(?:\.\d+)?", version):

        return failure_result(
            stage="input",
            reason=(
                "Document version must be a semantic label such as '1' or '1.1'."
            ),
        )

    logger.info(
        "RAG request | global_version=%s",
        version,
    )

    # ========================================================
    # STEP 0: FOLLOW-UP QUESTION REWRITING (memory support)
    # ========================================================
    #
    # If the frontend sent prior conversation turns, the raw
    # `question` might be elliptical ("what about that?"). We
    # rewrite it into a standalone question BEFORE retrieval,
    # so vector search actually finds the right chunks. If
    # there's no history, this is a no-op.

    retrieval_question = question

    needs_rewrite = bool(
        history
        and any(
            marker in question.lower()
            for marker in (
                " it",
                " that",
                " this",
                " them",
                " they",
                " what about",
                " how about",
            )
        )
    )

    if RAG_ENABLE_QUERY_REWRITE and needs_rewrite:

        try:

            from generation.generator import (
                rewrite_query_with_history
            )

            retrieval_question = rewrite_query_with_history(
                question,
                history,
            )

            if retrieval_question != question:
                logger.info(
                    "Rewrote follow-up question | "
                    "original=%r | rewritten=%r | "
                    "history_turns=%s",
                    question,
                    retrieval_question,
                    [
                        {
                            "question": turn.get("question", ""),
                            "answer": turn.get("answer", "")[:120],
                        }
                        for turn in history
                    ],
                )

        except Exception:

            logger.exception(
                "Query rewriting failed; using the "
                "original question."
            )
            retrieval_question = question

    # ========================================================
    # STEP 1: RETRIEVAL
    # ========================================================

        # ========================================================
    # STEP 1: RETRIEVAL QUERY EXPANSION
    # ========================================================
    #
    # Keep the original user question as the primary query.
    # Additional queries are only alternate phrasings used to
    # improve document retrieval. They are NEVER treated as
    # factual evidence.
    
    retrieval_queries = [
        retrieval_question
    ]

    try:

        from generation.generator import (
            generate_retrieval_queries
        )

        expanded_queries = generate_retrieval_queries(
            retrieval_question
        )

        if expanded_queries:
            retrieval_queries = expanded_queries

    except Exception:

        logger.exception(
            "Retrieval query expansion failed; "
            "using the original question."
        )

        retrieval_queries = [
            retrieval_question
        ]

    # Always make sure the original question is included.
    if retrieval_question not in retrieval_queries:

        retrieval_queries.insert(
            0,
            retrieval_question
        )

    # Remove duplicates while preserving order.
    retrieval_queries = list(
        dict.fromkeys(
            query.strip()
            for query in retrieval_queries
            if isinstance(query, str)
            and query.strip()
        )
    )

    logger.info(
        "Retrieval queries | original=%r | variants=%r",
        retrieval_question,
        retrieval_queries,
    )


    # ========================================================
    # STEP 2: MULTI-QUERY RETRIEVAL
    # ========================================================

    try:

        from retrieval.retrieval import (
            retrieve_many
        )

        retrieval_result = retrieve_many(

            queries=retrieval_queries,

            version=version,

            snapshot_data=snapshot_data,

            role=role,

        )

    except Exception as error:

        logger.exception(
            "RAG retrieval failed."
        )

        return failure_result(

            stage="retrieval",

            reason=str(error),

            version=version,

        )
    # --------------------------------------------------------
    # Relevance gate
    # --------------------------------------------------------

    if not retrieval_result.get(
        "has_evidence",
        False,
    ):

        return failure_result(
            stage="retrieval",
            reason=(
                "No sufficiently relevant "
                "documentation found."
            ),
            version=version,
        )

    results = retrieval_result.get(
        "results",
        [],
    )

    context = retrieval_result.get(
        "context",
        "",
    )

    if not results:

        return failure_result(
            stage="retrieval",
            reason=(
                "Retriever returned no evidence."
            ),
            version=version,
        )

    if not context.strip():

        return failure_result(
            stage="retrieval",
            reason=(
                "Retriever returned empty context."
            ),
            version=version,
        )

    # --------------------------------------------------------
    # Defensive version check.
    #
    # Retrieval already performs this check, but the RAG
    # orchestration layer verifies the metadata again.
    # --------------------------------------------------------

    retrieved_version = (
        retrieval_result.get(
            "version"
        )
    )

    if retrieved_version != version:

        return failure_result(
            stage="retrieval",
            reason=(
                "Retriever returned an unexpected "
                "document version."
            ),
            version=version,
        )

    # ========================================================
    # STEP 2: GENERATION
    # ========================================================

    try:

        from generation.generator import (
            generate_answer
        )

        generation_result = generate_answer(

            retrieval_question,

            context,
        )

    except Exception as error:

        logger.exception(
            "RAG generation failed."
        )

        return failure_result(
            stage="generation",
            reason=str(error),
            version=version,
        )

    # --------------------------------------------------------
    # Generator refusal
    # --------------------------------------------------------

    if not generation_result.get(
        "answerable",
        False,
    ):

        return failure_result(
            stage="generation",
            reason=(
                "Generator determined that the "
                "documentation does not contain "
                "enough information."
            ),
            version=version,
        )

    answer = generation_result.get(
        "answer",
        "",
    )

    claims = generation_result.get(
        "claims",
        [],
    )

    if not answer.strip():

        return failure_result(
            stage="generation",
            reason=(
                "Generator returned an empty answer."
            ),
            version=version,
        )

    # ========================================================
    # STEP 3: SOURCE VALIDATION
    # ========================================================

    try:

        validation_started_at = time.perf_counter()
        validate_generated_claims(

            claims,

            context,
        )
        timed("claim_validation", validation_started_at)

    except Exception as error:

        logger.exception(
            "Generated source validation failed."
        )

        return failure_result(
            stage="source_validation",
            reason=str(error),
            version=version,
        )

    # ========================================================
    # STEP 4: CLAIM VERIFICATION
    # ========================================================

    try:

        from generation.verifier import (
            verify_answer
        )

        verification = verify_answer(

            question=retrieval_question,

            answer=answer,

            claims=claims,

            context=context,
        )

    except Exception as error:

        logger.exception(
            "RAG verification failed."
        )

        return failure_result(
            stage="verification",
            reason=str(error),
            version=version,
        )

    # ========================================================
    # STEP 5: FINAL FAIL-CLOSED CHECK
    # ========================================================

    try:

        verified = (
            validate_verification_result(

                verification,

                context,
            )
        )

    except Exception as error:

        logger.exception(
            "Final verification validation failed."
        )

        return failure_result(
            stage="verification",
            reason=str(error),
            version=version,
        )

    if not verified:

        logger.warning(
            "VERIFICATION REJECTED | question=%r | answer=%r | "
            "unsupported_claims=%r | claims=%r",
            retrieval_question,
            answer,
            verification.get("unsupported_claims"),
            verification.get("claims"),
        )

        return failure_result(
            stage="verification",
            reason=(
                "One or more generated claims "
                "were not supported by the "
                "documentation."
            ),
            version=version,
        )

    # ========================================================
    # STEP 6: BUILD PUBLIC RESPONSE
    # ========================================================

    sources = build_sources(
        retrieval_result
    )

    return success_result(

        answer=answer,

        sources=sources,
    )


# ============================================================
# API-FRIENDLY HEALTH CHECK
# ============================================================

def health_check() -> Dict[str, Any]:
    """
    Basic health check for the RAG service.

    This does not call:

        - MySQL-backed vector search
        - LLM generation
        - query embedding
    """

    return {
        "status": "ok",
        "service": "strict-rag",
    }


# ============================================================
# TERMINAL TEST MODE
# ============================================================

def main():

    print("=" * 70)
    print("STRICT VERSION-AWARE RAG PIPELINE")
    print("=" * 70)

    question = input(
        "\nEnter your question: "
    ).strip()

    version_input = input(
        "Enter global version: "
    ).strip()

    if not version_input.isdigit():

        raise ValueError(
            "Document version must be an integer."
        )

    result = answer_question(

        query=question,

        version=int(
            version_input
        ),
    )

    print()
    print("=" * 70)
    print("RAG RESPONSE")
    print("=" * 70)

    print()
    print(
        f"Success: "
        f"{result['success']}"
    )

    print()
    print(
        f"Answer: "
        f"{result['answer']}"
    )

    # ========================================================
    # DEVELOPMENT DIAGNOSTICS
    # ========================================================

    if result.get(
        "_error"
    ):

        print()
        print(
            "Internal diagnostic:"
        )

        print(
            result["_error"]
        )

    # ========================================================
    # SOURCES
    # ========================================================

    if result.get(
        "sources"
    ):

        print()
        print("Sources:")

        for index, source in enumerate(
            result["sources"],
            start=1,
        ):

            path = " > ".join(
                source.get(
                    "heading_path",
                    [],
                )
            )

            print()
            print(
                f"{index}. {path}"
            )

            print(
                f"   Document ID: "
                f"{source.get('document_id')}"
            )

            print(
                f"   Version: "
                f"{source.get('version_number')}"
            )

            print(
                f"   Chunk ID: "
                f"{source.get('chunk_id')}"
            )

            print(
                f"   Relevance: "
                f"{source.get('relevance', 0):.4f}"
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()