from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import (
    DATABASE_URL,
)


# ============================================================
# BASE
# ============================================================

Base = declarative_base()


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(

    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(

    bind=engine,

    autoflush=False,

    autocommit=False,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():
    

    from database.models import (
        Document,
        DocumentVersion,
        Role,
        RoleDocumentAccess,
        SnapshotDocument,
        VersionSnapshot,
    )

    Base.metadata.create_all(
        bind=engine,
    )



# ============================================================
# SESSION HELPER
# ============================================================

def get_session():

    return SessionLocal()