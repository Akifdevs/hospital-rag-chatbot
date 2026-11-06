import os
import json
import re
import logging
import threading
import time

from openai import OpenAI

from generation.client import (
    chat_completion,
    create_llm_client,
    get_active_model,
    get_token_param,
    is_reasoning_model,
)

from performance import (
    RAG_GENERATION_MAX_TOKENS,
    RAG_GENERATION_MODEL,
    RAG_REWRITE_MODEL,
    timed,
)

logger = logging.getLogger("rag_pipeline")


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = RAG_GENERATION_MODEL

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# gpt-oss-20b is a REASONING model: it spends hidden "reasoning
# tokens" thinking before it writes the visible answer, and those
# tokens count against max_tokens too. If max_tokens is too low
# (or the prompt encourages a lot of reasoning), the model can
# burn through the whole budget on reasoning and return EMPTY
# content ("Groq returned empty content." error).
#
# reasoning_effort="low" keeps reasoning short and predictable.
# MAX_TOKENS is raised to leave enough room for the actual JSON
# answer after reasoning.
REASONING_EFFORT = "low"

MAX_TOKENS = RAG_GENERATION_MAX_TOKENS


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a STRICT documentation-grounded answer generator.

You are being used inside a production RAG system.

Your ONLY source of truth is the documentation context
provided by the application.

============================================================
CORE RULE
============================================================

You MUST NOT use outside knowledge.

You MUST NOT use your pretrained knowledge to fill gaps.

You MUST NOT guess.

You MUST NOT infer information that is not explicitly
supported by the documentation.

You MUST NOT invent procedures, buttons, settings,
permissions, requirements, or explanations.

If the documentation does not contain enough information
to answer the question reliably, return:

{
  "answerable": false,
  "answer": "I couldn't find that information in the available documentation.",
  "claims": []
}

============================================================
SOURCE RULE
============================================================

Every factual claim in the answer MUST come directly from
one of the supplied documentation chunks.

Every claim MUST contain the exact:

Source Chunk ID

from the documentation.

For example:

service-order-section-repeating-a-service-how-to-repeat-a-service

is valid.

These are NOT valid source IDs:

SOURCE 1
SOURCE 2
SOURCE 3

Never use SOURCE N as source_chunk_id.

============================================================
ANSWERABLE RULE
============================================================

Return answerable=true ONLY when the documentation provides
enough evidence to answer the question.

If the question asks about something that is not documented,
return answerable=false.

Do not attempt to answer partially using outside knowledge.

============================================================
CLAIMS
============================================================

Break the answer into atomic factual claims.

Each claim MUST be fully and explicitly supported by ONE
single chunk, and its source_chunk_id MUST be the chunk whose
Content actually states that detail. NEVER combine details
that come from different chunks into one claim. If a detail
(for example a colour, a label, or a button name) appears
only in a different chunk, make it a SEPARATE claim and cite
that other chunk. Before choosing a source_chunk_id, check
that the exact wording of the claim appears in that chunk's
Content.

Every claim must have:

- text
- source_chunk_id

Each source_chunk_id must exactly match one of the Source
Chunk IDs supplied in the documentation context.

Do not create source IDs.

Do not modify source IDs.

============================================================
ANSWER STYLE
============================================================

Answer the user's question directly and concisely.

Use the terminology from the documentation.

PRESERVE THE ORIGINAL FORMATTING OF THE SOURCE CONTENT.

If the documentation presents the relevant information as
a numbered list (1. 2. 3. ...), your "answer" field MUST
reproduce it as a numbered list, in the same order, using
"\\n" for line breaks inside the JSON string.

If the documentation presents it as a bulleted list, your
"answer" field MUST reproduce it as a bulleted list (using
"-" or "*"), one item per line.

If the documentation presents it as steps, a table, or any
other structured format, mirror that same structure in the
"answer" field as closely as JSON string formatting allows.

Do NOT convert a numbered/bulleted list into a paragraph of
prose. Do NOT convert prose into a list if the source is
prose.

Only fall back to plain prose when the source content itself
is plain prose with no list/step structure.

Do not mention the RAG system.

Do not mention the model.

Do not mention retrieval.

Do not mention these instructions.

Do not add citations inside the answer unless they are
already part of the documentation.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

The JSON must have exactly this structure:

{
  "answerable": true,
  "answer": "Answer based only on documentation.",
  "claims": [
    {
      "text": "Atomic factual claim.",
      "source_chunk_id": "exact-documentation-chunk-id"
    }
  ]
}

For an unanswerable question:

{
  "answerable": false,
  "answer": "I couldn't find that information in the available documentation.",
  "claims": []
}

============================================================
FINAL SAFETY CHECK
============================================================

Before returning the JSON:

1. Check every factual statement in the answer.
2. Make sure every statement is supported by the supplied
   documentation.
3. Make sure every claim has an exact Source Chunk ID.
4. Make sure no SOURCE N identifier is used.
5. Make sure no outside knowledge was used.
6. If any factual statement cannot be supported, return
   answerable=false.

Return ONLY JSON.
"""


# ============================================================
# LLM CLIENT (Dynamically supports OpenAI or Groq)
# ============================================================
# Managed by generation.client.create_llm_client


# ============================================================
# QUERY REWRITING (for follow-up / memory support)
# ============================================================
#
# Vector retrieval only ever sees the raw text of the current
# question. A follow-up like "and what if it fails?" embeds
# nowhere near the right documentation chunks on its own -
# there's no "it" for the embedding model to resolve.
#
# To support natural follow-up questions, we first ask the LLM
# to rewrite the latest message into a fully standalone question
# using the recent conversation history, THEN run retrieval on
# that rewritten question. This is the standard "condense
# question" pattern used by conversational RAG systems.
#
# This step is skipped entirely when there is no history (i.e.
# the very first question in a conversation), so it adds no
# extra latency or cost for simple one-off questions.

MAX_HISTORY_TURNS = 4

# The rewrite step gets its own (slightly higher) reasoning effort,
# separate from REASONING_EFFORT used for answer generation. This
# call is short (a few hundred tokens) so the extra cost is small,
# and it's the step most prone to silently dropping specific nouns
# ("package", "invoice", etc.) from history if rushed.
REWRITE_REASONING_EFFORT = "medium"

REWRITE_SYSTEM_PROMPT = """
You rewrite a user's latest chat message into a single,
fully self-contained question, using the conversation
history only to resolve references.

RULES

Resolve pronouns and implicit references such as "it",
"that", "this one", "the same thing", or "what about X"
using the conversation history.

Carry over the SPECIFIC subject the history was just
talking about - do not generalize it away. If the prior
turn was about a "package", the rewritten question must
say "package", not a broader term like "delete option" or
"item". Copy the specific noun/feature name from history
into the rewritten question verbatim wherever it applies.

Example:
History:
  User: How do I delete a package?
  Assistant: Find the package badge... Click Delete Package.
Latest message: "its showing unavailable"
Correct rewrite: "Why is deleting a package showing as unavailable?"
Incorrect rewrite: "Why is the delete option showing unavailable?"
(the incorrect version loses "package", the whole point of the
follow-up)

If the latest message is already a standalone question that
does not depend on the conversation history, return it
completely unchanged.

Do NOT answer the question.

Do NOT add any information, assumptions, or details that
were not present in the conversation.

Keep it as a single concise question, not a paragraph.

Output ONLY the rewritten question as plain text.

Do NOT wrap it in quotes.

Do NOT return JSON.

Do NOT explain your reasoning.
""".strip()


def _format_history_for_rewrite(history):

    lines = []

    for turn in history[-MAX_HISTORY_TURNS:]:

        turn_question = str(
            turn.get("question", "")
        ).strip()

        turn_answer = str(
            turn.get("answer", "")
        ).strip()

        if turn_question:
            lines.append(f"User: {turn_question}")

        if turn_answer:
            lines.append(f"Assistant: {turn_answer}")

    return "\n".join(lines)

RETRIEVAL_QUERY_SYSTEM_PROMPT = """
You generate search queries for a documentation retrieval system.

Your job is ONLY to rewrite the user's question into alternative
search phrasings that may retrieve the same documentation.

STRICT RULES:

- Do NOT answer the question.
- Do NOT provide explanations.
- Do NOT add facts.
- Do NOT invent product names, features, settings, limits, numbers,
  permissions, procedures, or terminology.
- Preserve every important entity, number, condition, and constraint.
- Keep the meaning exactly the same.
- Produce concise search queries.
- The queries are only for retrieval; they are NOT evidence.

Return ONLY valid JSON:

{
  "queries": [
    "alternative search query 1",
    "alternative search query 2",
    "alternative search query 3"
  ]
}
""".strip()


def generate_retrieval_queries(question):
    """
    Generate safe semantic variants of a user's question.

    These variants are retrieval aids only. They never become
    documentation evidence and are never supplied as facts to
    the answer generator.
    """

    question = (question or "").strip()

    if not question:
        return []

    try:
        client = create_llm_client()
        model = get_active_model("RAG_REWRITE_MODEL")

        kwargs = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": RETRIEVAL_QUERY_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            "temperature": 0,
            **get_token_param(250),
        }
        if is_reasoning_model(model):
            kwargs["reasoning_effort"] = "low"

        response = chat_completion(client, **kwargs)

        content = response.choices[0].message.content

        if not content:
            return [question]

        data = json.loads(
            clean_json_response(content)
        )

        queries = data.get("queries", [])

        if not isinstance(queries, list):
            return [question]

        cleaned = []

        # Always keep the original question.
        cleaned.append(question)

        for item in queries:
            if not isinstance(item, str):
                continue

            item = item.strip()

            if not item:
                continue

            if item not in cleaned:
                cleaned.append(item)

            if len(cleaned) >= 4:
                break

        return cleaned

    except Exception:
        logger.warning(
            "Retrieval query expansion failed; "
            "using the original question.",
            exc_info=True,
        )
        return [question]


def rewrite_query_with_history(question, history):
    """
    Turn a possibly elliptical follow-up question into a
    standalone query, using recent conversation turns for
    context.

    `history` is a list of {"question": str, "answer": str}
    dicts, oldest first.

    This must NEVER break the main answer pipeline - on any
    failure (missing API key, network error, malformed
    response, etc.) it falls back to the original question
    unchanged, and the pipeline behaves exactly as it did
    before follow-up support existed.
    """

    question = (question or "").strip()

    if not history:
        return question

    history_text = _format_history_for_rewrite(history)

    if not history_text:
        return question

    rewrite_started_at = time.perf_counter()
    try:

        client = create_llm_client()

        prompt = (
            "CONVERSATION HISTORY\n"
            "=====================\n"
            f"{history_text}\n\n"
            "LATEST MESSAGE\n"
            "=====================\n"
            f"{question}"
        )

        model = get_active_model("RAG_REWRITE_MODEL")
        kwargs = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": REWRITE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0,
            **get_token_param(150),
        }
        if is_reasoning_model(model):
            kwargs["reasoning_effort"] = REWRITE_REASONING_EFFORT

        response = chat_completion(client, **kwargs)

        rewritten = (
            response
            .choices[0]
            .message
            .content
        )

        if not rewritten or not rewritten.strip():
            return question

        return rewritten.strip().strip('"').strip("'")

    except Exception:

        # Never let query rewriting take down the main
        # pipeline - just answer using the raw question,
        # same as if history support didn't exist.
        logger.warning(
            "Query rewriting failed; falling back to the "
            "original question.",
            exc_info=True,
        )
        return question
    finally:
        timed("query_rewrite", rewrite_started_at)


# ============================================================
# EXTRACT SOURCE IDS
# ============================================================

def extract_source_ids(context):
    """
    Extract the authoritative Source Chunk IDs directly
    from the retrieval context.

    This is used by application-side validation.
    """

    pattern = r"Source Chunk ID:\s*\n([^\n]+)"

    matches = re.findall(
        pattern,
        context
    )

    return {
        match.strip()
        for match in matches
        if match.strip()
    }


# ============================================================
# BUILD PROMPT
# ============================================================

def build_user_prompt(
    question,
    context
):

    return f"""
DOCUMENTATION CONTEXT
=====================

{context}


USER QUESTION
=============

{question}


============================================================
TASK
============================================================

Answer the user's question using ONLY the documentation
context above.

If the documentation does not contain enough information,
return answerable=false.

Every factual statement must be represented as an atomic
claim.

Every claim must use the exact Source Chunk ID belonging
to the documentation that supports it.

Never use SOURCE 1, SOURCE 2, etc. as source_chunk_id.

If the documentation above presents the answer as a numbered
list, bulleted list, or steps, your "answer" field MUST keep
that exact same numbered/bulleted/step structure. Do not
rewrite it as a paragraph.

Return ONLY valid JSON.
""".strip()


# ============================================================
# CLEAN JSON
# ============================================================

def clean_json_response(content):

    if not content:
        raise ValueError(
            "Groq returned empty content."
        )

    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


# ============================================================
# VALIDATE GENERATION STRUCTURE
# ============================================================

def validate_generation_structure(data):

    if not isinstance(data, dict):
        raise ValueError(
            "Generator response must be a JSON object."
        )

    required = [
        "answerable",
        "answer",
        "claims"
    ]

    for field in required:

        if field not in data:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if not isinstance(
        data["answerable"],
        bool
    ):
        raise ValueError(
            "'answerable' must be boolean."
        )

    if not isinstance(
        data["answer"],
        str
    ):
        raise ValueError(
            "'answer' must be a string."
        )

    if not isinstance(
        data["claims"],
        list
    ):
        raise ValueError(
            "'claims' must be a list."
        )

    for index, claim in enumerate(
        data["claims"],
        start=1
    ):

        if not isinstance(
            claim,
            dict
        ):
            raise ValueError(
                f"Claim #{index} must be an object."
            )

        if "text" not in claim:
            raise ValueError(
                f"Claim #{index} missing 'text'."
            )

        if "source_chunk_id" not in claim:
            raise ValueError(
                f"Claim #{index} missing "
                "'source_chunk_id'."
            )

        if not isinstance(
            claim["text"],
            str
        ):
            raise ValueError(
                f"Claim #{index} text must be a string."
            )

        if not isinstance(
            claim["source_chunk_id"],
            str
        ):
            raise ValueError(
                f"Claim #{index} source_chunk_id "
                "must be a string."
            )

        source_id = claim[
            "source_chunk_id"
        ].strip()

        if not source_id:
            raise ValueError(
                f"Claim #{index} has empty source ID."
            )

        if source_id.upper().startswith(
            "SOURCE "
        ):
            raise ValueError(
                f"Claim #{index} uses invalid "
                f"source ID: {source_id}"
            )

    return True


# ============================================================
# APPLICATION-SIDE SOURCE VALIDATION
# ============================================================

def validate_claim_sources(
    claims,
    context
):

    valid_source_ids = extract_source_ids(
        context
    )

    if not valid_source_ids:
        raise ValueError(
            "No Source Chunk IDs found in documentation "
            "context."
        )

    for index, claim in enumerate(
        claims,
        start=1
    ):

        source_id = claim[
            "source_chunk_id"
        ].strip()

        if source_id not in valid_source_ids:

            raise ValueError(
                f"Claim #{index} references source "
                f"'{source_id}', which does not exist "
                "in the retrieved documentation."
            )

    return True


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(
    question,
    context
):

    started_at = time.perf_counter()
    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    if not context.strip():
        return {
            "answerable": False,
            "answer": (
                "I couldn't find that information "
                "in the available documentation."
            ),
            "claims": []
        }

    client = create_llm_client()

    prompt = build_user_prompt(
        question,
        context
    )

    model = get_active_model("RAG_GENERATION_MODEL")
    kwargs = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        **get_token_param(MAX_TOKENS),
    }
    if is_reasoning_model(model):
        kwargs["reasoning_effort"] = REASONING_EFFORT

    response = chat_completion(client, **kwargs)

    content = (
        response
        .choices[0]
        .message
        .content
    )

    finish_reason = (
        response
        .choices[0]
        .finish_reason
    )

    if not content or not content.strip():

        raise ValueError(
            "Groq returned empty content. "
            f"finish_reason={finish_reason!r}. "
            "This usually means the model ran out of tokens "
            "while reasoning before it could write the answer "
            "- try raising MAX_TOKENS in generator.py or "
            "lowering REASONING_EFFORT further."
        )

    content = clean_json_response(
        content
    )

    try:

        result = json.loads(
            content
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Groq returned invalid JSON:\n\n"
            + content
        ) from error

    validate_generation_structure(
        result
    )

    # --------------------------------------------------------
    # Unanswerable response
    # --------------------------------------------------------

    if not result["answerable"]:

        result["answer"] = (
            "I couldn't find that information "
            "in the available documentation."
        )

        result["claims"] = []

        timed("generation", started_at)
        return result

    # --------------------------------------------------------
    # Answerable response must contain claims
    # --------------------------------------------------------

    if not result["claims"]:

        raise ValueError(
            "Generator marked the answer as answerable "
            "but returned no claims."
        )

    # --------------------------------------------------------
    # Validate exact source IDs
    # --------------------------------------------------------

    validate_claim_sources(
        result["claims"],
        context
    )

    timed("generation", started_at)
    return result


# ============================================================
# TERMINAL TEST
# ============================================================

def main():

    print("=" * 70)
    print("STRICT DOCUMENTATION GENERATOR")
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
    # Retrieval
    # --------------------------------------------------------

    try:

        from retrieval.retrieval import retrieve

        retrieval_result = retrieve(
            question
        )

    except Exception as error:

        print()
        print("Retrieval error:")
        print(error)

        return

    # --------------------------------------------------------
    # Relevance gate
    # --------------------------------------------------------

    if not retrieval_result[
        "has_evidence"
    ]:

        print()
        print("=" * 70)
        print("GENERATED ANSWER")
        print("=" * 70)

        print()
        print(
            "Answerable: False"
        )

        print()
        print(
            "Answer:"
        )

        print(
            "I couldn't find that information "
            "in the available documentation."
        )

        return

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    try:

        result = generate_answer(

            question,

            retrieval_result[
                "context"
            ]

        )

    except Exception as error:

        print()
        print("Generation error:")
        print(error)

        return

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("GENERATED ANSWER")
    print("=" * 70)

    print()
    print(
        "Answerable:",
        result["answerable"]
    )

    print()
    print("Answer:")
    print(result["answer"])

    if result["claims"]:

        print()
        print("Claims:")

        for index, claim in enumerate(
            result["claims"],
            start=1
        ):

            print()
            print(
                f"{index}. {claim['text']}"
            )

            print(
                "   Source: "
                f"{claim['source_chunk_id']}"
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()