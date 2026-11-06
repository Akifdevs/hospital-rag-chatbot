import os
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent
)


DATA_DIR = (
    BASE_DIR
    / "data"
)


# ============================================================
# ENVIRONMENT FILE
# ============================================================

ENV_FILE = (
    BASE_DIR
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# APPLICATION
# ============================================================

SERVICE_NAME = os.getenv(
    "SERVICE_NAME",
    "strict-rag",
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development",
)

API_VERSION = os.getenv(
    "API_VERSION",
    "1.0.0",
)


# ============================================================
# DATABASE & VECTOR STORE
# ============================================================

MYSQL_HOST = os.getenv(
    "MYSQL_HOST",
    "127.0.0.1",
)

MYSQL_PORT = int(
    os.getenv(
        "MYSQL_PORT",
        "3306",
    )
)

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "service_rag")

DEFAULT_DATABASE_URL = (
    "mysql+pymysql://"
    f"{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    DEFAULT_DATABASE_URL,
)


# ============================================================
# DOCUMENT STORAGE
# ============================================================

DOCUMENT_STORAGE_MODE = os.getenv(
    "DOCUMENT_STORAGE_MODE",
    "local",
).strip().lower()


DOCUMENT_STORAGE_PATH = Path(
    os.getenv(
        "DOCUMENT_STORAGE_PATH",
        str(
            DATA_DIR
            / "documents"
        ),
    )
)


# ============================================================
# CORS
# ============================================================

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:3000,"
    "http://127.0.0.1:5173"
)


ALLOWED_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        DEFAULT_ALLOWED_ORIGINS,
    ).split(",")
    if origin.strip()
]


# ============================================================
# VALIDATION
# ============================================================

def validate_settings():
    """
    Validate infrastructure configuration.

    This function validates configuration only.
    It does not connect to external services.
    """

    # ========================================================
    # DOCUMENT STORAGE
    # ========================================================

    if not DATABASE_URL.startswith("mysql+pymysql://"):
        raise ValueError(
            "DATABASE_URL must use the MySQL PyMySQL dialect: "
            "mysql+pymysql://..."
        )


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

def get_settings_summary():
    """
    Return safe configuration information for diagnostics.
    """

    return {
        "service_name": SERVICE_NAME,

        "environment": ENVIRONMENT,

        "api_version": API_VERSION,

        "database_url": DATABASE_URL,

        "mysql_host": MYSQL_HOST,

        "mysql_port": MYSQL_PORT,

        "mysql_database": MYSQL_DATABASE,

        "document_storage_mode": (
            DOCUMENT_STORAGE_MODE
        ),

        "document_storage_path": (
            str(
                DOCUMENT_STORAGE_PATH
            )
        ),

        "allowed_origins": (
            ALLOWED_ORIGINS
        ),
    }