import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from fastapi.middleware.cors import CORSMiddleware

from rag_pipeline import answer_question

from database.connection import get_session, init_database
from database.repository import DocumentRepository
from auth.roles import (
    resolve_request_role,
    get_allowed_document_version_ids_for_role,
    get_role_allowed_documents_count,
)
from performance import (
    RAG_AUTO_INGEST,
    RAG_INGEST_DEBOUNCE_SECONDS,
    RAG_INGEST_SOURCE_SET_GLOB,
    RAG_INGEST_WATCH_INTERVAL_SECONDS,
    RAG_INGEST_WATCH_ROOT,
    RAG_ENABLE_CACHE,
    RAG_WARMUP_EMBEDDING_MODEL,
    answer_cache,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("strict-rag-api")


# ============================================================
# CONFIGURATION
# ============================================================

SERVICE_NAME = "strict-rag"

API_VERSION = "1.0.0"

# Plain greetings ("hi", "hii", "hello", "hey there", "good
# morning", ...) get a short canned reply instead of going through
# document retrieval + generation. This only fires when the WHOLE
# message is just a greeting (+ optional punctuation/emoji) - a
# message like "hi, how do I cancel an order?" still goes through
# the normal RAG pipeline.
GREETING_WORDS = (
    r"hi+|hey+|hello+|hola|yo|sup|"
    r"good\s?morning|good\s?afternoon|good\s?evening|"
    r"namaste|namaskar"
)

GREETING_PATTERN = re.compile(
    rf"^\s*(?:{GREETING_WORDS})"
    rf"(?:\s*[,!.\s]\s*(?:{GREETING_WORDS}))*"
    rf"[\s!.?]*$",
    re.IGNORECASE,
)

GREETING_REPLY = (
    "Hey there! 👋 I'm your AI Assistant - ask me anything about the "
    "documentation and I'll help you find the answer."
)


def is_pure_greeting(question: str) -> bool:
    """
    True only when the ENTIRE message is a greeting (optionally
    repeated / punctuated), not just when it starts with one.
    """

    return bool(GREETING_PATTERN.match(question.strip()))


# ------------------------------------------------------------
# Acknowledgements / thanks / goodbyes ("ok", "thank you", "bye")
# ------------------------------------------------------------
# Like greetings, these never need document retrieval. A message
# qualifies ONLY when every word is from the small vocabularies
# below AND at least one "core" word is present, so real short
# questions ("is it good?", "what is this") are never swallowed.

THANKS_REPLY = (
    "You're welcome! 😊 Let me know if you have any other questions."
)

ACK_REPLY = (
    "Great! 👍 Feel free to ask if there's anything else I can help with."
)

BYE_REPLY = (
    "Goodbye! 👋 Come back anytime if you have more questions."
)

_SMALLTALK_PHRASES = (
    ("thank you", "thankyou"),
    ("got it", "gotit"),
    ("i see", "isee"),
    ("makes sense", "makessense"),
    ("that's all", "thatsall"),
    ("thats all", "thatsall"),
    ("that's it", "thatsall"),
    ("thats it", "thatsall"),
    ("good night", "goodnight"),
    ("take care", "takecare"),
    ("see you", "seeyou"),
    ("no problem", "noproblem"),
)

_THANKS_WORDS = {
    "thanks", "thanx", "thankyou", "thx", "ty", "tysm", "cheers",
    "appreciate", "appreciated", "shukriya", "shukriyaa",
    "dhanyavad", "dhanyavaad",
}

_BYE_WORDS = {
    "bye", "byee", "byebye", "goodbye", "goodnight", "takecare",
    "seeyou", "cya", "tata", "gn", "alvida",
}

_ACK_WORDS = {
    "ok", "okay", "okk", "okkk", "k", "kk", "alright", "fine",
    "great", "cool", "nice", "perfect", "awesome", "good",
    "understood", "noted", "sure", "hmm", "hmmm", "gotit", "isee",
    "makessense", "thatsall", "noproblem", "done", "yes", "yeah",
    "yep", "yup", "no", "nope", "nahi", "haan", "theek", "thik",
    "achha", "accha", "acha", "bas",
}

# Allowed alongside the words above but never enough on their own.
_SMALLTALK_FILLER = {
    "so", "much", "a", "lot", "very", "again", "ji", "sir", "madam",
    "mam", "buddy", "bro", "man", "you", "your", "for", "the",
    "help", "helpful", "helped", "really", "all", "that", "this",
    "nothing", "else", "more", "enough", "hai", "oh", "ohh", "right",
    "it", "i", "to", "now",
}

_SMALLTALK_EMOJI_PATTERN = re.compile(
    r"^[\s👍🙏😊😀🙂😄👌❤️✌️🤝🙌👏]+$"
)


def get_smalltalk_reply(question: str) -> Optional[str]:
    """
    Return a short canned reply when the WHOLE message is just an
    acknowledgement, thanks, or goodbye. Otherwise return None so
    the message goes through the normal RAG pipeline.
    """

    text = question.strip()

    if not text:
        return None

    if _SMALLTALK_EMOJI_PATTERN.match(text):
        return THANKS_REPLY

    lowered = text.lower()

    for phrase, token in _SMALLTALK_PHRASES:
        lowered = lowered.replace(phrase, token)

    words = re.findall(r"[a-z]+", lowered)

    if not words or len(words) > 8:
        return None

    allowed = (
        _THANKS_WORDS
        | _BYE_WORDS
        | _ACK_WORDS
        | _SMALLTALK_FILLER
    )

    if any(word not in allowed for word in words):
        return None

    if any(word in _BYE_WORDS for word in words):
        return BYE_REPLY

    if any(word in _THANKS_WORDS for word in words):
        return THANKS_REPLY

    if any(word in _ACK_WORDS for word in words):
        return ACK_REPLY

    return None


VERSION_EXTRACTION_PATTERN = re.compile(r"\bversion\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)

# Only the literal "version N" phrase is removed here. Deliberately NOT
# trying to also strip the filler words around it ("I want ... from",
# "switch to", "using", etc.) - enumerating every possible phrasing in
# one regex is brittle (see the "answer" vs "answers" bug this replaced).
# Leftover filler words are harmless to retrieval/embedding, and whether
# the message contains a REAL question is judged separately below by
# has_meaningful_content(), which is robust to phrasing because it works
# off a stopword list instead of a hand-built alternation pattern.
VERSION_STRIP_PATTERN = re.compile(r"\bversion\s+\d+(?:\.\d+)?\b", re.IGNORECASE)

# Words that carry no question content on their own. Used only to judge
# whether a message has an actual question in it once version-related
# instructions are set aside - NOT used to alter the text sent to
# retrieval, so it's safe to be generous here.
FILLER_WORDS = {
    "i", "me", "my", "you", "your", "we", "our", "it", "its",
    "want", "wants", "wanted", "need", "needs", "needed",
    "now", "please", "give", "get", "can", "could", "would", "should",
    "switch", "change", "set", "use", "using", "answer", "answers",
    "reply", "response", "from", "in", "on", "at", "to", "for",
    "with", "about", "of", "the", "a", "an", "this", "that",
    "is", "are", "do", "does", "and", "or", "to", "go", "just",
}

# How many non-filler words must remain before we treat a message as
# containing a real question, as opposed to just a version instruction.
MIN_MEANINGFUL_WORDS = 2


def extract_version_from_query(query: str) -> Optional[str]:
    match = VERSION_EXTRACTION_PATTERN.search(query)
    if match:
        return match.group(1)
    return None


def strip_version_from_query(query: str) -> str:
    """
    Remove the "version N" phrase and conversational lead-ins like
    "in version 1, " or whole version-only declaration lines from the query.
    """
    lines = [line.strip() for line in query.splitlines() if line.strip()]
    cleaned_lines = []
    for line in lines:
        sub_line = VERSION_STRIP_PATTERN.sub("", line)
        words = re.findall(r"[a-zA-Z0-9']+", sub_line.lower())
        meaningful = [w for w in words if w not in FILLER_WORDS]
        if meaningful:
            cleaned_lines.append(line)

    text = " ".join(cleaned_lines) if cleaned_lines else query

    text = re.sub(
        r"\b(?:now\s+)?(?:in|from|for|using|with)?\s*version\s+\d+(?:\.\d+)?\s*[,:;-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = VERSION_STRIP_PATTERN.sub("", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([?.!,;:])", r"\1", text)
    text = text.strip(" \t\n\r,;:-")
    return text


def has_meaningful_content(text: str) -> bool:
    """
    True if, after discarding filler/stopwords, the text still contains
    at least MIN_MEANINGFUL_WORDS words of actual question content.

    This is what decides whether a message like "I want answers from
    version 1" is a real question or just a version instruction with
    nothing to search for - regardless of exactly how the version
    instruction is phrased.
    """
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    meaningful = [word for word in words if word not in FILLER_WORDS]
    return len(meaningful) >= MIN_MEANINGFUL_WORDS


DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:3000,"
    "http://127.0.0.1:5173"
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        DEFAULT_ALLOWED_ORIGINS,
    ).split(",")
    if origin.strip()
]


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Strict Documentation RAG API",
    description=(
        "Documentation-grounded question answering API. "
        "Answers are returned only after retrieval, "
        "generation, source validation, and claim verification."
    ),
    version=API_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_source_watcher = None


def _migrate_version_snapshot_schema() -> None:
    """
    Add major_version / minor_version / version_label columns to the
    version_snapshots table if they do not already exist, then backfill
    any legacy rows that still have the sentinel default value '?'.

    Safe to call on every startup — each ALTER TABLE is silently ignored
    if the column already exists.
    """
    from sqlalchemy import text
    from database.connection import engine  # the raw SQLAlchemy engine

    with engine.connect() as conn:
        for col, ddl in [
            ("major_version", "INTEGER NOT NULL DEFAULT 1"),
            ("minor_version", "INTEGER NOT NULL DEFAULT 0"),
            ("version_label", "TEXT NOT NULL DEFAULT '?'"),
        ]:
            try:
                conn.execute(text(
                    f"ALTER TABLE version_snapshots ADD COLUMN {col} {ddl}"
                ))
                conn.commit()
            except Exception:
                # Column already exists — skip silently.
                conn.rollback()

        # Backfill rows that still have the sentinel label '?'
        # (rows created before this migration ran, keyed by their old
        # integer version_number: 1 -> "1", 2 -> "2", etc.).
        conn.execute(text(
            "UPDATE version_snapshots "
            "SET major_version = version_number, "
            "    minor_version = 0, "
            "    version_label = CAST(version_number AS TEXT) "
            "WHERE version_label = '?'"
        ))
        conn.commit()

    logger.info("version_snapshots schema migration complete")


@app.on_event("startup")
def initialize_database_schema():
    """
    Initialize database/application infrastructure.

    IMPORTANT:
    Application startup NEVER creates a document version.

    Global document-set versions are created only through the
    explicit register_and_ingest_documents.py command.
    """

    init_database()

    

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # Do NOT start an ingestion watcher here.
    #
    # Startup must be completely independent from global
    # document version creation.
    #
    # If a detection watcher is desired later, it can be
    # started here without an ingestion callback.
    #
    # For now, no watcher is started by the API.
    #
    # --------------------------------------------------------

    logger.info(
        "Application startup complete | "
        "automatic document ingestion disabled"
    )


@app.on_event("shutdown")
def close_shared_clients():

    global _source_watcher

    if _source_watcher is not None:

        _source_watcher.stop()
        _source_watcher = None

    from retrieval.retrieval import (
        close_vector_store,
    )

    close_vector_store()
# ============================================================
# REQUEST ID MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):
    """
    Generate or preserve a request ID for every HTTP request.

    If the client provides:

        X-Request-ID

    that ID is preserved.

    Otherwise, a new UUID is generated.

    The same ID is:

    1. Stored on request.state
    2. Available to endpoint handlers
    3. Returned in the X-Request-ID response header
    """

    request_id = (
        request.headers.get(
            "X-Request-ID"
        )
        or str(uuid.uuid4())
    )

    request.state.request_id = request_id

    response = await call_next(
        request
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatHistoryTurn(BaseModel):
    """
    One prior exchange in the current conversation, sent by the
    frontend so follow-up questions ("what about X?", "and if it
    fails?") can be understood in context.

    Only question/answer text is needed here - no need for
    timestamps or IDs, since this is used purely to resolve
    references in the LATEST question, not stored server-side.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    answer: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    version: Optional[Union[int, float, str]] = Field(
        default=None,
        description="Optional version established in this turn.",
    )

    @field_validator("version", mode="before")
    @classmethod
    def normalize_history_version(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        label = str(v).strip()
        # Accept "N" or "N.M" only
        if not re.match(r"^\d+(\.\d+)?$", label):
            raise ValueError("version must be 'N' or 'N.M' format")
        # Normalise "1.0" -> "1"
        if label.endswith(".0"):
            label = label[:-2]
        return label

    model_config = ConfigDict(extra="forbid")


def extract_version_from_history(
    history: List[ChatHistoryTurn],
) -> Optional[str]:
    """
    Look back through prior conversation turns (most recent first)
    to find the most recent semantic global version label.
    """
    for turn in reversed(history):
        if turn.version is not None:
            return str(turn.version)
        extracted = extract_version_from_query(turn.question)
        if extracted is not None:
            return extracted
    return None


class ChatRequest(BaseModel):
    """
    Request received from the frontend.

    The caller selects one complete global document snapshot.
    The answer is always generated from that exact version set.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's documentation query.",
    )

    version: Optional[Union[int, float, str]] = Field(
        default=None,
        description=(
            "Global document-set version to answer from. "
            "Accepts an integer (e.g. 1), a string label (e.g. '1.1'), "
            "or omit to fall back to query/history extraction."
        ),
    )

    url: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=4096,
        description=(
            "Full URL of the browser page embedding the chat widget. "
            "Supplied as request metadata; it does not affect retrieval."
        ),
    )

    role: Optional[str] = Field(
        default=None,
        max_length=50,
        description=(
            "User role read by the widget from the browser's localStorage. "
            "Client-declared, so it is NOT secure on its own."
        ),
    )

    @field_validator("version", mode="before")
    @classmethod
    def normalize_version(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        label = str(v).strip()
        # Accept "N" or "N.M" only
        if not re.match(r"^\d+(\.\d+)?$", label):
            raise ValueError("version must be 'N' or 'N.M' format")
        # Normalise "1.0" -> "1"
        if label.endswith(".0"):
            label = label[:-2]
        return label

    history: List[ChatHistoryTurn] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Recent prior turns in this conversation, oldest "
            "first. Used only to resolve follow-up questions "
            "into standalone queries - not stored server-side."
        ),
    )

    model_config = ConfigDict(extra="forbid")


# ============================================================
# RESPONSE MODELS
# ============================================================

class ChatResponse(BaseModel):

    success: bool

    answer: str

    error: Optional[str] = None

    request_id: str


class DocumentSummary(BaseModel):
    """
    Public representation of a logical document.

    This intentionally does not expose the complete
    SQLAlchemy object.
    """

    id: int

    document_number: str

    name: str

    description: Optional[str] = None


class DocumentVersionResponse(BaseModel):
    """
    Public representation of a READY document version.

    Only versions that can safely be queried by the RAG
    system are returned by the version endpoints.
    """

    id: int

    version_number: int

    file_name: str

    status: str

    is_latest: bool

    chunk_count: int


class DocumentVersionsResponse(BaseModel):

    document_id: int

    versions: List[
        DocumentVersionResponse
    ]


class DocumentDetailResponse(BaseModel):

    id: int

    document_number: str

    name: str

    description: Optional[str] = None

    versions: List[
        DocumentVersionResponse
    ]


class DocumentListResponse(BaseModel):

    documents: List[
        DocumentSummary
    ]


class VersionSnapshotResponse(BaseModel):

    version: str
    version_label: str

    major_version: int

    minor_version: int

    status: str

    document_count: int


class VersionSnapshotListResponse(BaseModel):

    versions: List[VersionSnapshotResponse]



# ============================================================
# ROOT
# ============================================================

@app.get("/")
@app.get("/api/v1/info")
def root() -> Dict[str, str]:

    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "version": API_VERSION,
        "environment": os.getenv(
            "ENVIRONMENT",
            "development",
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health() -> Dict[str, str]:

    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }


# ============================================================
# READINESS CHECK
# ============================================================

@app.get("/ready")
def ready() -> Dict[str, str]:

    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        # ----------------------------------------------------
        # At least one successfully indexed version must exist.
        # ----------------------------------------------------

        documents = (
            repository.list_documents()
        )

        for document in documents:

            versions = (
                repository.list_ready_versions(
                    document.id
                )
            )

            if versions:

                return {
                    "status": "ready",
                    "service": SERVICE_NAME,
                }

        return {
            "status": "not_ready",
            "service": SERVICE_NAME,
            "reason": (
                "No ready document "
                "versions available."
            ),
        }

    except Exception:

        logger.exception(
            "Readiness check failed."
        )

        return {
            "status": "not_ready",
            "service": SERVICE_NAME,
            "reason": (
                "Database readiness check failed."
            ),
        }

    finally:

        session.close()


# ============================================================
# DOCUMENT LIST
# ============================================================

@app.get(
    "/api/v1/documents",
    response_model=DocumentListResponse,
)
def list_documents() -> DocumentListResponse:
    """
    Return all logical documents stored in the database.

    This endpoint allows the frontend to dynamically discover
    available documentation instead of hardcoding document IDs.
    """

    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        documents = (
            repository.list_documents()
        )

        result = []

        for document in documents:

            result.append(
                DocumentSummary(
                    id=document.id,

                    document_number=(
                        document.document_number
                    ),

                    name=document.name,

                    description=(
                        document.description
                    ),
                )
            )

        return DocumentListResponse(
            documents=result
        )

    except Exception:

        logger.exception(
            "Failed to list documents."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve documents.",
        )

    finally:

        session.close()


@app.get(
    "/api/v1/versions",
    response_model=VersionSnapshotListResponse,
)
def list_versions() -> VersionSnapshotListResponse:
    """Return global document-set snapshots available for chat."""

    session = get_session()

    try:
        repository = DocumentRepository(session)
        snapshots = repository.list_snapshots(ready_only=True)
        return VersionSnapshotListResponse(
            versions=[
                VersionSnapshotResponse(
                    version=snapshot.version_label,
                    version_label=snapshot.version_label,
                    major_version=snapshot.major_version,
                    minor_version=snapshot.minor_version,
                    status=snapshot.status,
                    document_count=len(snapshot.documents),
                )
                for snapshot in snapshots
            ]
        )
    finally:
        session.close()



# ============================================================
# DOCUMENT DETAIL
# ============================================================

@app.get(
    "/api/v1/documents/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document(
    document_id: int,
) -> DocumentDetailResponse:
    """
    Return a document and all of its READY versions.

    Processing versions are intentionally not exposed as
    selectable RAG versions.
    """

    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        document = (
            repository.get_document(
                document_id
            )
        )

        if document is None:

            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        versions = (
            repository.list_ready_versions(
                document_id
            )
        )

        version_results = []

        for version in versions:

            version_results.append(
                DocumentVersionResponse(

                    id=version.id,

                    version_number=(
                        version.version_number
                    ),

                    file_name=(
                        version.file_name
                    ),

                    status=(
                        version.status
                    ),

                    is_latest=(
                        version.is_latest
                    ),

                    chunk_count=(
                        version.chunk_count
                    ),
                )
            )

        return DocumentDetailResponse(

            id=document.id,

            document_number=(
                document.document_number
            ),

            name=document.name,

            description=(
                document.description
            ),

            versions=version_results,
        )

    except HTTPException:

        raise

    except Exception:

        logger.exception(
            "Failed to retrieve document | "
            "document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve document.",
        )

    finally:

        session.close()


# ============================================================
# DOCUMENT VERSIONS
# ============================================================

@app.get(
    "/api/v1/documents/{document_id}/versions",
    response_model=DocumentVersionsResponse,
)
def list_document_versions(
    document_id: int,
) -> DocumentVersionsResponse:
    """
    Return READY versions for one document.

    The frontend can use this endpoint to populate its
    documentation-version selector.
    """

    session = get_session()

    try:

        repository = (
            DocumentRepository(
                session
            )
        )

        document = (
            repository.get_document(
                document_id
            )
        )

        if document is None:

            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        versions = (
            repository.list_ready_versions(
                document_id
            )
        )

        result = []

        for version in versions:

            result.append(
                DocumentVersionResponse(

                    id=version.id,

                    version_number=(
                        version.version_number
                    ),

                    file_name=(
                        version.file_name
                    ),

                    status=(
                        version.status
                    ),

                    is_latest=(
                        version.is_latest
                    ),

                    chunk_count=(
                        version.chunk_count
                    ),
                )
            )

        return DocumentVersionsResponse(

            document_id=document_id,

            versions=result,
        )

    except HTTPException:

        raise

    except Exception:

        logger.exception(
            "Failed to list document versions | "
            "document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve "
                "document versions."
            ),
        )

    finally:

        session.close()


# ============================================================
# INTERNAL CHAT HANDLER
# ============================================================

def process_chat(
    request: ChatRequest,
    request_id: str,
    http_request: Optional[Request] = None,
) -> ChatResponse:

    # The role comes from the request payload (the widget reads it from
    # localStorage). The X-User-Role header is still accepted as a fallback.
    role = resolve_request_role(request.role or http_request)
    allowed_docs_count = get_role_allowed_documents_count(role, documentation_version=request.version)
    logger.info(
        "Chat request received | request_id=%s | role=%s | allowed_docs_count=%d | explicit_version=%s",
        request_id,
        role,
        allowed_docs_count,
        request.version,
    )

    question = request.query.strip()

    if not question:
        return ChatResponse(
            success=False,
            answer=(
                "Please enter a question about "
                "the service documentation."
            ),
            error="invalid_request",
            request_id=request_id,
        )

    # Small talk ("hi", "hii", "hello", ...) is answered directly,
    # skipping document retrieval and generation entirely - there's
    # nothing in the docs to look up for a greeting, and it keeps
    # these replies fast and cheap.
    if is_pure_greeting(question):
        logger.info(
            "Greeting short-circuit | request_id=%s",
            request_id,
        )
        return ChatResponse(
            success=True,
            answer=GREETING_REPLY,
            error=None,
            request_id=request_id,
        )

    # Acknowledgements ("ok", "thank you", "bye", ...) are also
    # answered directly - no retrieval, no version needed.
    smalltalk_reply = get_smalltalk_reply(question)
    if smalltalk_reply is not None:
        logger.info(
            "Small-talk short-circuit | request_id=%s",
            request_id,
        )
        return ChatResponse(
            success=True,
            answer=smalltalk_reply,
            error=None,
            request_id=request_id,
        )

    # Resolve version: explicit request.version takes priority if provided,
    # otherwise attempt regex extraction from question text.
    # Resolve version priority:
    # a) request.version (explicit field) — if set, always wins.
    # b) Version extracted from current query text.
    # a) request.version (explicit field) — after the validator runs, this
    #    is already a canonical str label (e.g. "1" or "1.1").
    # b) Version extracted from current query text as a semantic label.
    # c) Most recent version established in conversation history.
    query_version = extract_version_from_query(question)
    history_version = extract_version_from_history(request.history)

    if request.version is not None:
        target_version = request.version
        # Already normalized to str by the field_validator.
        target_version: Optional[str] = request.version  # type: ignore[assignment]
        version_source = "explicit_request"
    elif query_version is not None:
        target_version = query_version
        version_source = "current_query"
    elif history_version is not None:
        target_version = history_version
        version_source = "history"
    else:
        target_version = None
        version_source = None

    # If NO version can be extracted and request.version is not set:
    # If NO version can be resolved:
    # (Defensive guard - this path should not be reachable when the
    # frontend always sends an explicit version field.)
    if target_version is None:
        try:
            with get_session() as session:
                repository = DocumentRepository(session)
                ready_snapshots = repository.list_snapshots(ready_only=True) if hasattr(repository, "list_snapshots") else []
                labels = [
                    f"Version {getattr(s, 'version_label', None) or getattr(s, 'version_number', '')}"
                    for s in ready_snapshots
                ]
                if labels:
                    versions_text = ", ".join(labels)
                    prompt = (
                        f"Please specify which version of the documentation you'd like me to answer from. "
                        f"Available versions: {versions_text}."
                    )
                else:
                    prompt = "Please specify which version of the documentation you'd like me to answer from."
        except Exception:
            prompt = "Please specify which version of the documentation you'd like me to answer from."

        logger.warning(
            "No documentation version resolved | request_id=%s | detail=%s",
            request_id,
            prompt,
        )
        return ChatResponse(
            success=False,
            answer=(
                "Sorry, I can't access the documentation right now. "
                "Please try again later."
            ),
            error="version_required",
            request_id=request_id,
        )

    # Convert integer strings like "1", "2" to int for backwards-compatibility
    # with existing tests and integer version lookups, while preserving "1.1" etc.
    target_version_lookup = (
        int(target_version)
        if (isinstance(target_version, int) or (isinstance(target_version, str) and target_version.isdigit()))
        else target_version
    )

    # Validate version exists and is ready
    try:
        with get_session() as session:
            repository = DocumentRepository(session)
            snapshot = repository.get_snapshot(
                target_version_lookup,
                ready_only=True,
            )

            if snapshot is None:
                ready_snapshots = repository.list_snapshots(ready_only=True) if hasattr(repository, "list_snapshots") else []
                labels = [
                    f"Version {getattr(s, 'version_label', None) or getattr(s, 'version_number', '')}"
                    for s in ready_snapshots
                ]
                if labels:
                    versions_text = ", ".join(labels)
                    answer = (
                        f"That documentation version isn't available right now. "
                        f"Available versions: {versions_text}."
                    )
                else:
                    answer = (
                        "That documentation version isn't available right now, "
                        "and there are no other versions available at this time."
                    )
                logger.warning(
                    "Requested documentation version unavailable | "
                    "request_id=%s | requested=%s | detail=%s",
                    request_id,
                    target_version,
                    answer,
                )
                return ChatResponse(
                    success=False,
                    answer=(
                        "Sorry, I can't access the documentation right "
                        "now. Please try again later."
                    ),
                    error="version_not_found",
                    request_id=request_id,
                )

            document_version_ids = get_allowed_document_version_ids_for_role(
                role_name=role,
                snapshot=snapshot,
                documentation_version=target_version_lookup,
            )
            snapshot_data = (snapshot, document_version_ids)
            version_label = getattr(snapshot, "version_label", None) or getattr(snapshot, "version_number", str(target_version_lookup))

        # Strip version phrase out of query
        cleaned_question = strip_version_from_query(question)
        if not has_meaningful_content(cleaned_question):
            return ChatResponse(
                success=False,
                answer=(
                    "Please type your question and I'll help you "
                    "find the answer in the documentation."
                ),
                error="invalid_request",
                request_id=request_id,
            )

        if RAG_ENABLE_CACHE and not request.history:
            cached_result = answer_cache.get(str(version_label), cleaned_question, role=role)
            if cached_result is not None:
                return _build_chat_response(
                    cached_result,
                    request_id,
                    version=str(version_label),
                )

        logger.info(
            "Resolved version | request_id=%s | "
            "version_label=%s | version_source=%s | cleaned_query=%r",
            request_id,
            version_label,
            version_source,
            cleaned_question,
        )

        result = answer_question(
            query=cleaned_question,
            version=target_version_lookup,
            snapshot_data=snapshot_data,
            history=[
                {"question": turn.question, "answer": turn.answer}
                for turn in request.history
            ],
            role=role,
        )

    except Exception:
        logger.exception(
            "RAG pipeline failed | request_id=%s | version=%s",
            request_id,
            target_version,
        )
        return ChatResponse(
            success=False,
            answer=(
                "Sorry, I ran into a problem while searching the "
                "documentation. Please try again in a moment."
            ),
            error="rag_service_error",
            request_id=request_id,
        )

    success = bool(result.get("success", False))
    if RAG_ENABLE_CACHE and success and not request.history:
        answer_cache.set(version_label, cleaned_question, result, role=role)

    return _build_chat_response(result, request_id, version=version_label)


def _build_chat_response(
    result: Dict[str, Any],
    request_id: str,
    version: Optional[str] = None,
) -> ChatResponse:
    success = bool(result.get("success", False))
    default_fallback = (
        "I couldn't find information about that in the documentation. "
        "Could you try rephrasing your question, or ask about "
        "something else I can help with?"
    )

    answer = str(result.get("answer") or default_fallback)
    if not success and version is not None and "clear answer" in answer:
        answer = default_fallback

    if not success:
        return ChatResponse(
            success=False,
            answer=answer,
            error="answer_not_available",
            request_id=request_id,
        )

    return ChatResponse(
        success=True,
        answer=answer,
        error=None,
        request_id=request_id,
    )


# ============================================================
# VERSIONED CHAT ENDPOINT
# ============================================================

@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
)
def chat_v1(
    request: ChatRequest,
    http_request: Request,
) -> ChatResponse:

    request_id = (
        http_request.state.request_id
    )

    return process_chat(
        request,
        request_id,
        http_request=http_request,
    )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat_legacy(
    request: ChatRequest,
    http_request: Request,
) -> ChatResponse:

    request_id = (
        http_request.state.request_id
    )

    return process_chat(
        request,
        request_id,
        http_request=http_request,
    )


# ============================================================
# WIDGET (built frontend, served from the same origin so it
# works over a single ngrok tunnel with no CORS setup needed)
# ============================================================

_FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"


@app.get("/widget.js", include_in_schema=False)
def serve_widget_js():
    """Serve the embeddable widget with an explicit JavaScript content type."""
    widget_file = _FRONTEND_DIST / "widget.js"
    if not widget_file.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "widget.js not found. Run 'npm run build:all' "
                "inside the frontend folder."
            ),
        )
    return FileResponse(
        str(widget_file),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )

if _FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="widget",
    )
