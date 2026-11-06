from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.connection import Base


# ============================================================
# DOCUMENT
# ============================================================

class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )


# ============================================================
# DOCUMENT VERSION
# ============================================================

class DocumentVersion(Base):

    __tablename__ = "document_versions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ready",
    )

    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="versions",
    )

    snapshot_documents: Mapped[List["SnapshotDocument"]] = relationship(
        "SnapshotDocument",
        back_populates="document_version",
        cascade="all, delete-orphan",
    )


# ============================================================
# GLOBAL VERSION SNAPSHOT
# ============================================================

class VersionSnapshot(Base):

    __tablename__ = "version_snapshots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ----------------------------------------------------------
    # version_number: legacy synthetic integer surrogate.
    # Kept to satisfy the existing NOT NULL + UNIQUE constraint
    # on older DB rows. New inserts should still auto-increment
    # this.  All human-facing version identification now uses
    # version_label / major_version / minor_version below.
    # ----------------------------------------------------------
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    # ----------------------------------------------------------
    # Semantic major.minor versioning.
    # Examples: "1" (major=1, minor=0), "1.1", "2".
    # version_label is the canonical human-facing identifier and
    # is the primary key used by the API and the CLI.
    # ----------------------------------------------------------
    major_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    minor_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    version_label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        default="?",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="processing",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ready_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    documents: Mapped[List["SnapshotDocument"]] = relationship(
        "SnapshotDocument",
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="SnapshotDocument.document_id",
    )


class SnapshotDocument(Base):

    __tablename__ = "snapshot_documents"

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "document_id",
            name="uq_snapshot_document",
        ),
        UniqueConstraint(
            "snapshot_id",
            "document_version_id",
            name="uq_snapshot_document_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey(
            "version_snapshots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    document_version_id: Mapped[int] = mapped_column(
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    snapshot: Mapped[VersionSnapshot] = relationship(
        "VersionSnapshot",
        back_populates="documents",
    )

    document_version: Mapped[DocumentVersion] = relationship(
        "DocumentVersion",
        back_populates="snapshot_documents",
    )


# ============================================================
# EMBEDDED CHUNK
# ============================================================

class Chunk(Base):

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    point_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
    )

    embedding: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ============================================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================

class Role(Base):

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    can_access_all: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document_access: Mapped[List["RoleDocumentAccess"]] = relationship(
        "RoleDocumentAccess",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class RoleDocumentAccess(Base):

    __tablename__ = "role_document_access"

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "document_identifier",
            "documentation_version",
            name="uq_role_document_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    document_identifier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    documentation_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="document_access",
    )

