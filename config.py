import os
from typing import List


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "Strict Documentation RAG API"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).lower()

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "service_rag")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}",
)


# ============================================================
# SERVER
# ============================================================

HOST = os.getenv(
    "HOST",
    "127.0.0.1"
)

PORT = int(
    os.getenv(
        "PORT",
        "8000"
    )
)


# ============================================================
# CORS
# ============================================================

def get_allowed_origins() -> List[str]:

    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    )

    origins = [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]

    return origins


ALLOWED_ORIGINS = get_allowed_origins()


# ============================================================
# API
# ============================================================

API_PREFIX = "/api/v1"

CHAT_MAX_LENGTH = int(
    os.getenv(
        "CHAT_MAX_LENGTH",
        "2000"
    )
)


# ============================================================
# RAG
# ============================================================

REFUSAL_MESSAGE = (
    "Hmm, I couldn't find a clear answer to that. "
    "Could you try rephrasing your question, or ask "
    "about something else I can help with?"
)