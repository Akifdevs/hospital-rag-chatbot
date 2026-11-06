import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

from openai import OpenAI

from generation.client import (
    chat_completion,
    create_llm_client,
    get_active_model,
    get_token_param,
)

from performance import (
    RAG_VERIFIER_MAX_TOKENS,
    RAG_VERIFIER_MODEL,
    timed,
)

logger = logging.getLogger("strict-rag-verifier")


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = RAG_VERIFIER_MODEL

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

MAX_TOKENS = RAG_VERIFIER_MAX_TOKENS

REFUSAL_MESSAGE = (
    "Hmm, I couldn't find a clear answer to that. "
    "Could you try rephrasing your question, or ask "
    "about something else I can help with?"
)


# ============================================================
# LLM CLIENT (Dynamically supports OpenAI or Groq)
# ============================================================
# Managed by generation.client.create_llm_client


# ============================================================
# VERIFICATION SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a STRICT factual verifier for a documentation
question-answering system.

Your job is NOT to answer the user's question.

Your ONLY job is to determine whether every factual claim
in the generated answer is directly supported by the
supplied documentation.

============================================================
STRICT RULES
============================================================

1. Use ONLY the supplied documentation.

2. Do NOT use general knowledge.

3. Do NOT use pretrained knowledge.

4. Do NOT assume information.

5. Do NOT infer facts that are not explicitly supported.

6. A claim is SUPPORTED only when the documentation
   explicitly supports the claim.

7. If a claim adds information that is not present in
   the documentation, mark it UNSUPPORTED.

8. If a claim is only partially supported, mark it
   UNSUPPORTED.

9. The source_chunk_id supplied with a claim is NOT
   evidence by itself.

10. Inspect the documentation content associated with the
    source_chunk_id FIRST. If that chunk does not contain the
    detail, but ANOTHER chunk in the supplied documentation
    EXPLICITLY states it, the claim is SUPPORTED. In that case,
    put the ID of the chunk that actually supports the claim
    in "source_chunk_id" of your output. A claim is
    UNSUPPORTED only if NO chunk in the supplied documentation
    explicitly supports it.

11. If the source_chunk_id does not exist in the supplied
    documentation, mark the claim UNSUPPORTED.

12. If ANY factual claim is unsupported, the entire
    answer must be rejected.

13. Do NOT repair the answer.

14. Do NOT rewrite the answer.

15. Do NOT add claims.

16. Do NOT remove claims.

17. Return ONLY valid JSON.

============================================================
SOURCE ID RULE
============================================================

Valid source IDs look like:

service-order-section-repeating-a-service-how-to-repeat-a-service

Invalid source IDs include:

SOURCE 1
SOURCE 2
SOURCE 3

Never treat SOURCE N as a real source ID.

============================================================
OUTPUT FORMAT
============================================================

Return exactly:

{
  "verified": true,
  "claims": [
    {
      "claim": "claim text",
      "source_chunk_id": "exact chunk id",
      "supported": true,
      "reason": "Why the documentation supports this claim."
    }
  ],
  "unsupported_claims": []
}

If ANY claim is unsupported:

{
  "verified": false,
  "claims": [
    {
      "claim": "claim text",
      "source_chunk_id": "exact chunk id",
      "supported": false,
      "reason": "Why the documentation does not support this claim."
    }
  ],
  "unsupported_claims": [
    "claim text"
  ]
}

============================================================
FAIL CLOSED
============================================================

When uncertain, mark the claim unsupported.

One unsupported factual claim means:

verified = false
"""


# ============================================================
# BUILD VERIFICATION PROMPT
# ============================================================

def build_verification_prompt(
    question: str,
    answer: str,
    claims: List[Dict[str, Any]],
    context: str
) -> str:

    claims_json = json.dumps(
        claims,
        indent=2,
        ensure_ascii=False
    )

    return f"""
DOCUMENTATION CONTEXT
=====================

{context}


USER QUESTION
=============

{question}


GENERATED ANSWER
================

{answer}


GENERATED CLAIMS
================

{claims_json}


============================================================
VERIFICATION TASK
============================================================

Evaluate every factual claim.

For each claim:

1. Find the source_chunk_id in the documentation.
2. Inspect the actual content of that source.
3. Determine whether the source explicitly supports
   the claim. If the cited source does not contain the
   detail, scan EVERY other SOURCE in the documentation
   context above before deciding. If any of them explicitly
   states it, the claim is supported (use that chunk's ID).
4. Mark supported=true only when the documentation
   provides sufficient evidence.

Do not use outside knowledge.

If every claim is supported:

verified = true

If even one claim is unsupported:

verified = false

Return ONLY valid JSON.
""".strip()


# ============================================================
# PARSE JSON RESPONSE
# ============================================================

def parse_json_response(
    response: str
) -> Dict[str, Any]:

    response = response.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:
        return json.loads(response)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Markdown code block
    # --------------------------------------------------------

    if response.startswith("```"):

        lines = response.splitlines()

        if len(lines) >= 3:

            content = "\n".join(
                lines[1:-1]
            )

            try:
                return json.loads(content)

            except json.JSONDecodeError:
                pass

    raise ValueError(
        "Verifier did not return valid JSON.\n\n"
        f"Raw response:\n{response}"
    )


# ============================================================
# VALIDATE VERIFICATION STRUCTURE
# ============================================================

def validate_verification(
    result: Dict[str, Any],
    original_claims: List[Dict[str, Any]]
) -> Dict[str, Any]:

    required_fields = {
        "verified",
        "claims",
        "unsupported_claims"
    }

    missing = (
        required_fields
        - result.keys()
    )

    if missing:

        raise ValueError(
            "Verifier response is missing fields: "
            f"{missing}"
        )

    if not isinstance(
        result["verified"],
        bool
    ):

        raise ValueError(
            "'verified' must be boolean."
        )

    if not isinstance(
        result["claims"],
        list
    ):

        raise ValueError(
            "'claims' must be a list."
        )

    if not isinstance(
        result["unsupported_claims"],
        list
    ):

        raise ValueError(
            "'unsupported_claims' must be a list."
        )

    # --------------------------------------------------------
    # FAIL CLOSED
    # --------------------------------------------------------

    if result["unsupported_claims"]:

        result["verified"] = False

    # --------------------------------------------------------
    # Generator had claims but verifier evaluated nothing
    # --------------------------------------------------------

    if original_claims and not result["claims"]:

        result["verified"] = False

        result["unsupported_claims"] = [
            "Verifier did not evaluate the generated claims."
        ]

    # --------------------------------------------------------
    # Every evaluated claim must be supported
    # --------------------------------------------------------

    for claim in result["claims"]:

        if not claim.get(
            "supported",
            False
        ):

            result["verified"] = False

    return result


# ============================================================
# APPLICATION-SIDE SOURCE VALIDATION
# ============================================================

def extract_source_ids(
    context: str
) -> set:

    source_ids = set()

    for line in context.splitlines():

        line = line.strip()

        if line.startswith(
            "Source Chunk ID:"
        ):
            continue

    lines = context.splitlines()

    for index, line in enumerate(lines):

        if line.strip() == "Source Chunk ID:":

            if index + 1 < len(lines):

                source_id = lines[
                    index + 1
                ].strip()

                if source_id:

                    source_ids.add(
                        source_id
                    )

    return source_ids


def validate_claim_source_ids(
    claims: List[Dict[str, Any]],
    context: str
):

    valid_source_ids = extract_source_ids(
        context
    )

    if not valid_source_ids:

        raise ValueError(
            "No source chunk IDs were found "
            "in the documentation context."
        )

    for index, claim in enumerate(
        claims,
        start=1
    ):

        source_id = claim.get(
            "source_chunk_id",
            ""
        ).strip()

        if not source_id:

            raise ValueError(
                f"Claim #{index} has no source_chunk_id."
            )

        if source_id.upper().startswith(
            "SOURCE "
        ):

            raise ValueError(
                f"Claim #{index} uses invalid "
                f"source ID: {source_id}"
            )

        if source_id not in valid_source_ids:

            raise ValueError(
                f"Claim #{index} references unknown "
                f"source chunk: {source_id}"
            )


# ============================================================
# VERIFY ANSWER
# ============================================================

def verify_answer(
    question: str,
    answer: str,
    claims: List[Dict[str, Any]],
    context: str
) -> Dict[str, Any]:

    started_at = time.perf_counter()

    if not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )

    if not answer.strip():

        raise ValueError(
            "Answer cannot be empty."
        )

    if not claims:

        raise ValueError(
            "Claims cannot be empty."
        )

    if not context.strip():

        raise ValueError(
            "Documentation context cannot be empty."
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # Validate source IDs BEFORE asking the LLM.
    # --------------------------------------------------------

    validate_claim_source_ids(
        claims,
        context
    )

    client = create_llm_client()

    prompt = build_verification_prompt(
        question=question,
        answer=answer,
        claims=claims,
        context=context
    )

    model = get_active_model("RAG_VERIFIER_MODEL")
    response = chat_completion(
        client,
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
        **get_token_param(MAX_TOKENS),
    )

    choice = response.choices[0]
    generated_text = choice.message.content

    if choice.finish_reason == "length":
        logger.warning(
            "Verifier response was truncated because max_tokens (%s) was reached. "
            "Consider increasing RAG_VERIFIER_MAX_TOKENS in .env.",
            MAX_TOKENS,
        )

    if not generated_text:

        raise ValueError(
            "Verifier returned an empty response."
        )

    result = parse_json_response(
        generated_text
    )

    result = validate_verification(
        result,
        claims
    )

    timed("verification", started_at)
    return result


# ============================================================
# FINAL DECISION
# ============================================================

def apply_verification(
    answer: str,
    verification: Dict[str, Any]
) -> str:

    if verification["verified"]:

        return answer

    return REFUSAL_MESSAGE


# ============================================================
# DISPLAY
# ============================================================

def display_verification(
    verification: Dict[str, Any]
):

    print()
    print("=" * 70)
    print("VERIFICATION RESULT")
    print("=" * 70)

    print()
    print(
        f"Verified: "
        f"{verification['verified']}"
    )

    for index, claim in enumerate(
        verification["claims"],
        start=1
    ):

        print()
        print(
            f"Claim #{index}"
        )

        print(
            f"Claim: "
            f"{claim.get('claim', '')}"
        )

        print(
            f"Source: "
            f"{claim.get('source_chunk_id', '')}"
        )

        print(
            f"Supported: "
            f"{claim.get('supported', False)}"
        )

        print(
            f"Reason: "
            f"{claim.get('reason', '')}"
        )

    if verification["unsupported_claims"]:

        print()
        print(
            "Unsupported claims:"
        )

        for claim in (
            verification["unsupported_claims"]
        ):

            print(
                f"- {claim}"
            )


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print("=" * 70)
    print("STRICT RAG VERIFIER")
    print("=" * 70)

    question = input(
        "\nEnter your question: "
    ).strip()

    if not question:

        print(
            "\nQuestion cannot be empty."
        )

        return

    # --------------------------------------------------------
    # Import retrieval and generator
    # --------------------------------------------------------

    try:

        from retrieval.retrieval import retrieve
        from generation.generator import generate_answer

    except Exception as error:

        print()
        print(
            "Import error:"
        )

        print(error)

        return

    # --------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------

    try:

        retrieval_result = retrieve(
            question
        )

    except Exception as error:

        print()
        print(
            "Retrieval error:"
        )

        print(error)

        return

    if not retrieval_result[
        "has_evidence"
    ]:

        print()
        print(
            "No sufficiently relevant "
            "documentation found."
        )

        return

    context = retrieval_result[
        "context"
    ]

    # --------------------------------------------------------
    # Generation
    # --------------------------------------------------------

    try:

        generation_result = generate_answer(
            question,
            context
        )

    except Exception as error:

        print()
        print(
            "Generation error:"
        )

        print(error)

        return

    if not generation_result[
        "answerable"
    ]:

        print()
        print(
            "The documentation does not contain "
            "enough information."
        )

        return

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    try:

        verification = verify_answer(

            question=question,

            answer=generation_result[
                "answer"
            ],

            claims=generation_result[
                "claims"
            ],

            context=context
        )

    except Exception as error:

        print()
        print(
            "Verification error:"
        )

        print(error)

        print()
        print(
            "Answer rejected."
        )

        return

    # --------------------------------------------------------
    # Display verification
    # --------------------------------------------------------

    display_verification(
        verification
    )

    # --------------------------------------------------------
    # Final answer
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL DECISION")
    print("=" * 70)

    final_answer = apply_verification(
        generation_result["answer"],
        verification
    )

    print()
    print(final_answer)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()