from rag_pipeline import (
    REFUSAL_MESSAGE,
    extract_context_source_ids,
    validate_generated_claims,
    validate_verification_result,
)


# ============================================================
# CONTEXT SOURCE EXTRACTION
# ============================================================

def test_extract_context_source_ids():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Heading:
First

Content:
First content.


SOURCE 2

Source Chunk ID:
chunk-two

Heading:
Second

Content:
Second content.
"""

    result = extract_context_source_ids(
        context
    )

    assert result == {
        "chunk-one",
        "chunk-two",
    }


# ============================================================
# VALID CLAIM
# ============================================================

def test_valid_generated_claim():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    claims = [
        {
            "text": (
                "Click Repeat."
            ),

            "source_chunk_id":
                "chunk-one"
        }
    ]

    assert validate_generated_claims(
        claims,
        context
    ) is True


# ============================================================
# INVALID SOURCE
# ============================================================

def test_claim_with_unknown_source_fails():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    claims = [
        {
            "text": (
                "Click Repeat."
            ),

            "source_chunk_id":
                "fake-source"
        }
    ]

    try:

        validate_generated_claims(
            claims,
            context
        )

        assert False, (
            "Expected source validation "
            "to fail."
        )

    except ValueError:

        pass


# ============================================================
# SOURCE NUMBER MUST NOT BE ACCEPTED
# ============================================================

def test_source_number_is_rejected():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    claims = [
        {
            "text": (
                "Click Repeat."
            ),

            "source_chunk_id":
                "SOURCE 1"
        }
    ]

    try:

        validate_generated_claims(
            claims,
            context
        )

        assert False, (
            "SOURCE 1 should not be "
            "accepted as a source ID."
        )

    except ValueError:

        pass


# ============================================================
# EMPTY CLAIMS
# ============================================================

def test_empty_claims_fail():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    try:

        validate_generated_claims(
            [],
            context
        )

        assert False

    except ValueError:

        pass


# ============================================================
# VERIFIED CLAIMS
# ============================================================

def test_verified_result():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    verification = {

        "verified": True,

        "claims": [

            {
                "claim":
                    "Click Repeat.",

                "source_chunk_id":
                    "chunk-one",

                "supported":
                    True,

                "reason":
                    "Explicitly documented."
            }
        ],

        "unsupported_claims": []
    }

    assert validate_verification_result(
        verification,
        context
    ) is True


# ============================================================
# UNSUPPORTED CLAIM
# ============================================================

def test_unsupported_claim_fails():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    verification = {

        "verified": True,

        "claims": [

            {
                "claim":
                    "Click Repeat.",

                "source_chunk_id":
                    "chunk-one",

                "supported":
                    False,

                "reason":
                    "Not supported."
            }
        ],

        "unsupported_claims": [
            "Click Repeat."
        ]
    }

    assert validate_verification_result(
        verification,
        context
    ) is False


# ============================================================
# VERIFIED WITHOUT CLAIMS
# ============================================================

def test_verified_without_claims_fails():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    verification = {

        "verified": True,

        "claims": [],

        "unsupported_claims": []
    }

    try:

        validate_verification_result(
            verification,
            context
        )

        assert False

    except ValueError:

        pass


# ============================================================
# UNKNOWN VERIFIER SOURCE
# ============================================================

def test_verifier_unknown_source_fails():

    context = """
SOURCE 1

Source Chunk ID:
chunk-one

Content:
Click Repeat.
"""

    verification = {

        "verified": True,

        "claims": [

            {
                "claim":
                    "Click Repeat.",

                "source_chunk_id":
                    "fake-source",

                "supported":
                    True
            }
        ],

        "unsupported_claims": []
    }

    try:

        validate_verification_result(
            verification,
            context
        )

        assert False

    except ValueError:

        pass