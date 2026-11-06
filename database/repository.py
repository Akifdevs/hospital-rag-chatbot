from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from database.models import (
    Document,
    DocumentVersion,
    Role,
    RoleDocumentAccess,
    SnapshotDocument,
    VersionSnapshot,
)


class DocumentRepository:

    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    # ========================================================
    # DOCUMENTS
    # ========================================================

    def create_document(
        self,
        document_number: str,
        name: str,
        description: Optional[str] = None,
    ) -> Document:

        document = Document(
            document_number=document_number,
            name=name,
            description=description,
        )

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        return document

    def get_document(
        self,
        document_id: int,
    ) -> Optional[Document]:

        return self.session.get(
            Document,
            document_id,
        )

    def get_document_by_number(
        self,
        document_number: str,
    ) -> Optional[Document]:

        statement = select(
            Document
        ).where(
            Document.document_number
            == document_number
        )

        return self.session.scalar(
            statement
        )

    def list_documents(
        self,
    ) -> list[Document]:
        """
        Return all documents stored in the database.

        Documents are ordered by document number.

        This method is intentionally database-backed so the
        API can dynamically discover any number of documents.
        """

        statement = (
            select(Document)
            .order_by(
                Document.document_number
            )
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )

    # ========================================================
    # VERSIONS
    # ========================================================

    def create_version(
        self,
        document_id: int,
        file_name: str,
        storage_key: str,
        sha256: str,
        chunk_count: int = 0,
        status: str = "processing",
    ) -> DocumentVersion:
        """
        Create the next version for a document.

        Version numbers are independent for each document.

        Example:

            Document 1045 -> v1, v2, v3
            Document 2050 -> v1, v2

        New versions are initially created as processing.

        They become latest only after successful ingestion
        through set_latest().
        """

        versions = self.list_versions(
            document_id
        )

        # ----------------------------------------------------
        # Determine next version number.
        # ----------------------------------------------------

        next_version = (
            max(
                version.version_number
                for version in versions
            ) + 1
            if versions
            else 1
        )

        # ----------------------------------------------------
        # First version becomes latest initially.
        #
        # Subsequent versions are promoted only after
        # successful ingestion.
        # ----------------------------------------------------

        version = DocumentVersion(
            document_id=document_id,
            version_number=next_version,
            file_name=file_name,
            storage_key=storage_key,
            sha256=sha256,
            status=status,
            is_latest=not versions,
            chunk_count=chunk_count,
        )

        self.session.add(
            version
        )

        self.session.commit()

        self.session.refresh(
            version
        )

        return version

    # ========================================================
    # GET VERSION
    # ========================================================

    def get_version(
        self,
        document_id: int,
        version_number: int,
    ) -> Optional[DocumentVersion]:

        statement = select(
            DocumentVersion
        ).where(
            DocumentVersion.document_id
            == document_id,

            DocumentVersion.version_number
            == version_number,
        )

        return self.session.scalar(
            statement
        )

    # ========================================================
    # GET READY VERSION
    # ========================================================

    def get_ready_version(
        self,
        document_id: int,
        version_number: int,
    ) -> Optional[DocumentVersion]:
        """
        Return a specific document version only when it is
        successfully indexed.

        The RAG query path must never retrieve from versions
        that are still processing or have failed.
        """

        statement = select(
            DocumentVersion
        ).where(
            DocumentVersion.document_id
            == document_id,

            DocumentVersion.version_number
            == version_number,

            DocumentVersion.status
            == "ready",
        )

        return self.session.scalar(
            statement
        )

    # ========================================================
    # GET VERSION BY SHA-256
    # ========================================================

    def get_version_by_sha256(
        self,
        document_id: int,
        sha256: str,
    ) -> Optional[DocumentVersion]:
        """
        Find an already successfully ingested version with
        the same document content.

        This provides ingestion idempotency.

        If the exact same file content was already indexed,
        the ingestion pipeline can skip:

            - chunking
            - embedding
            - MySQL chunk and embedding insertion
        """

        statement = select(
            DocumentVersion
        ).where(
            DocumentVersion.document_id
            == document_id,

            DocumentVersion.sha256
            == sha256,

            DocumentVersion.status
            == "ready",
        )

        return self.session.scalar(
            statement
        )

    # ========================================================
    # GET LATEST VERSION
    # ========================================================

    def get_latest_version(
        self,
        document_id: int,
    ) -> Optional[DocumentVersion]:
        """
        Return the latest READY version of a document.

        The database is the source of truth for the latest
        version.
        """

        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.status == "ready",
            )
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )

        return self.session.scalar(statement)

    # ========================================================
    # LIST ALL VERSIONS
    # ========================================================

    def list_versions(
        self,
        document_id: int,
    ) -> list[DocumentVersion]:
        """
        Return every version belonging to a document.

        This includes:

            processing
            ready
            failed

        versions.

        It is primarily used by the ingestion system.
        """

        statement = (
            select(
                DocumentVersion
            )
            .where(
                DocumentVersion.document_id
                == document_id
            )
            .order_by(
                DocumentVersion.version_number
            )
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )

    # ========================================================
    # LIST READY VERSIONS
    # ========================================================

    def list_ready_versions(
        self,
        document_id: int,
    ) -> list[DocumentVersion]:
        """
        Return only successfully indexed versions.

        Processing and failed versions are intentionally
        excluded because they are not available for RAG
        retrieval.
        """

        statement = (
            select(
                DocumentVersion
            )
            .where(
                DocumentVersion.document_id
                == document_id,

                DocumentVersion.status
                == "ready",
            )
            .order_by(
                DocumentVersion.version_number
            )
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )

    # ========================================================
    # VERSION STATUS
    # ========================================================

    def update_version_status(
        self,
        version_id: int,
        status: str,
        chunk_count: Optional[int] = None,
    ) -> DocumentVersion:
        """
        Update the ingestion status of a document version.

        When a version becomes ready, indexed_at is recorded.
        """

        version = self.session.get(
            DocumentVersion,
            version_id,
        )

        if version is None:

            raise ValueError(
                "Document version does not exist."
            )

        version.status = status

        if chunk_count is not None:

            version.chunk_count = (
                chunk_count
            )

        if status == "ready":

            version.indexed_at = (
                datetime.now(
                    timezone.utc
                )
            )

        self.session.commit()

        self.session.refresh(
            version
        )

        return version

    # ========================================================
    # SET LATEST
    # ========================================================

    def set_latest(
        self,
        document_id: int,
        version_number: int,
    ) -> DocumentVersion:
        """
        Promote a READY document version to latest.

        Only one version for a document can be latest.

        The previous latest version is automatically
        demoted.
        """

        version = self.get_version(
            document_id,
            version_number,
        )

        if version is None:

            raise ValueError(
                "Document version does not exist."
            )

        # ----------------------------------------------------
        # Only READY versions can become latest.
        # ----------------------------------------------------

        if version.status != "ready":

            raise ValueError(
                "Only a ready document version "
                "can be marked as latest."
            )

        # ----------------------------------------------------
        # Remove latest flag from every other version of
        # this document.
        # ----------------------------------------------------

        self.session.execute(
            update(
                DocumentVersion
            )
            .where(
                DocumentVersion.document_id
                == document_id
            )
            .values(
                is_latest=False
            )
        )

        # ----------------------------------------------------
        # Promote requested version.
        # ----------------------------------------------------

        version.is_latest = True

        # ----------------------------------------------------
        # Update parent document timestamp.
        # ----------------------------------------------------

        document = self.get_document(
            document_id
        )

        if document:

            document.updated_at = (
                datetime.now(
                    timezone.utc
                )
            )

        self.session.commit()

        self.session.refresh(
            version
        )

        return version

    # ========================================================
    # GLOBAL VERSION SNAPSHOTS
    # ========================================================

    def create_snapshot(
        self,
        document_versions: dict[int, int],
        major_version: Optional[int] = None,
        minor_version: Optional[int] = None,
        version_label: Optional[str] = None,
        status: str = "ready",
    ) -> VersionSnapshot:
        """
        Create one global version snapshot containing one READY revision
        for every logical document in ``document_versions``.

        The mapping is ``document_id -> document_version_id``.
        Existing document revisions are intentionally reused so
        unchanged documents can be carried into a new snapshot.

        ``version_number`` (the old integer surrogate) is still
        auto-incremented to satisfy the NOT NULL + UNIQUE constraint on
        the existing column.  ``version_label`` is the semantic key.

        Snapshots are created READY by default so a successfully indexed
        document set is immediately queryable.
        """
        if not document_versions:
            raise ValueError(
                "A snapshot must contain at least one document."
            )

       

        # Check if an existing snapshot matches this exact document mapping
        for s in self.list_snapshots():
            s_map = {doc.document_id: doc.document_version_id for doc in s.documents}
            if s_map == document_versions:
                return s

        if major_version is None:
            latest_snap = self.session.scalar(
                select(VersionSnapshot).order_by(
                    VersionSnapshot.version_number.desc()
                ).limit(1)
            )
            next_num = (latest_snap.version_number + 1) if latest_snap else 1
            major_version = next_num
            minor_version = 0

        if minor_version is None:
            minor_version = 0

        if version_label is None:
            version_label = f"{major_version}" if minor_version == 0 else f"{major_version}.{minor_version}"

        # ----------------------------------------------------------
        # Idempotency guard: a semantic version label is unique.
        # ----------------------------------------------------------
        existing = self.session.scalar(
            select(VersionSnapshot).where(
                VersionSnapshot.version_label == version_label
            )
        )
        if existing is not None and existing.status != "pending_review":
            raise ValueError(
                f"A snapshot with version_label='{version_label}' already "
                f"exists with status='{existing.status}'."
            )

        # ----------------------------------------------------------
        # Validate that every document_version_id is READY and maps
        # to the correct document.
        # ----------------------------------------------------------
        for document_id, document_version_id in document_versions.items():
            document_version = self.session.get(
                DocumentVersion,
                document_version_id,
            )
            if document_version is None:
                raise ValueError(
                    f"Document version {document_version_id} does not exist."
                )
            if document_version.document_id != document_id:
                raise ValueError(
                    "Snapshot document/version mapping does not match."
                )
            if document_version.status != "ready":
                raise ValueError(
                    "Snapshots can only contain ready document versions."
                )

        # ----------------------------------------------------------
        # Backward compatibility for a snapshot created by the old
        # pending-review workflow. Replace its document mapping with
        # the newly ingested READY revisions and publish it immediately.
        # ----------------------------------------------------------
        if existing is not None:
            existing.documents.clear()
            self.session.flush()

            for document_id, document_version_id in document_versions.items():
                existing.documents.append(
                    SnapshotDocument(
                        document_id=document_id,
                        document_version_id=document_version_id,
                    )
                )

            existing.status = "ready"
            existing.ready_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        # ----------------------------------------------------------
        # Determine next synthetic version_number (legacy surrogate).
        # ----------------------------------------------------------
        latest_number = self.session.scalar(
            select(VersionSnapshot.version_number).order_by(
                VersionSnapshot.version_number.desc()
            ).limit(1)
        )
        next_number = (latest_number or 0) + 1

        snapshot = VersionSnapshot(
            version_number=next_number,
            major_version=major_version,
            minor_version=minor_version,
            version_label=version_label,
            status=status,
            ready_at=(
                datetime.now(timezone.utc)
                if status == "ready"
                else None
            ),
        )
        self.session.add(snapshot)
        self.session.flush()

        for document_id, document_version_id in document_versions.items():
            snapshot.documents.append(
                SnapshotDocument(
                    document_id=document_id,
                    document_version_id=document_version_id,
                )
            )

        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def get_snapshot(
        self,
        version_label: str,
        ready_only: bool = False,
    ) -> Optional[VersionSnapshot]:
        """
        Look up a snapshot by its human-facing ``version_label``
        (e.g. ``"1"``, ``"1.1"``, ``"2"``).
        """
        statement = select(VersionSnapshot).where(
            VersionSnapshot.version_label == str(version_label)
        )
        if ready_only:
            statement = statement.where(
                VersionSnapshot.status == "ready"
            )
        return self.session.scalar(statement)

    def get_pending_review_snapshot(self) -> Optional["VersionSnapshot"]:
        """
        Return the newest legacy ``pending_review`` snapshot, if one exists.

        New ingestion no longer creates pending snapshots. This method is
        retained only for backward compatibility with older deployments.
        """
        return self.session.scalar(
            select(VersionSnapshot)
            .where(VersionSnapshot.status == "pending_review")
            .order_by(
                VersionSnapshot.major_version.desc(),
                VersionSnapshot.minor_version.desc(),
            )
            .limit(1)
        )

    def list_snapshots(
        self,
        ready_only: bool = True,
    ) -> list[VersionSnapshot]:
        statement = select(VersionSnapshot)

        if ready_only:
            statement = statement.where(
                VersionSnapshot.status == "ready"
            )

        # Sort semantically by (major, minor) — NOT by the legacy
        # version_number integer surrogate, which would give wrong
        # ordering for labels like "1.1", "1.2", "2".
        statement = statement.order_by(
            VersionSnapshot.major_version,
            VersionSnapshot.minor_version,
        )

        return list(self.session.scalars(statement).all())

    def get_snapshot_document_version_ids(
        self,
        snapshot_id: int,
    ) -> list[int]:
        statement = select(
            SnapshotDocument.document_version_id
        ).where(
            SnapshotDocument.snapshot_id == snapshot_id
        )

        return list(self.session.scalars(statement).all())

    def get_snapshot_identities(
        self,
        snapshot_id: int,
    ) -> set[str]:
        """
        Return the set of document titles (``Document.name``) for all
        documents included in a snapshot.

        Used by ``decide_next_version_label()`` to compare the incoming
        document identity set against the last confirmed snapshot.
        """
        statement = (
            select(Document.name)
            .join(SnapshotDocument, SnapshotDocument.document_id == Document.id)
            .where(SnapshotDocument.snapshot_id == snapshot_id)
        )
        return set(self.session.scalars(statement).all())

    def update_snapshot_document(
        self,
        snapshot_id: int,
        document_id: int,
        new_document_version_id: int,
    ) -> None:
        """
        Replace the ``document_version_id`` for a given
        ``(snapshot_id, document_id)`` pair in ``SnapshotDocument``.

        Legacy compatibility helper for older callers. New ingestion creates
        a fresh READY global snapshot instead of updating a draft in-place.
        """
        snap_doc = self.session.scalar(
            select(SnapshotDocument).where(
                SnapshotDocument.snapshot_id == snapshot_id,
                SnapshotDocument.document_id == document_id,
            )
        )
        if snap_doc is None:
            # Document not yet in this draft — add it.
            self.session.add(
                SnapshotDocument(
                    snapshot_id=snapshot_id,
                    document_id=document_id,
                    document_version_id=new_document_version_id,
                )
            )
        else:
            snap_doc.document_version_id = new_document_version_id

        self.session.commit()

    def update_snapshot_status(
        self,
        snapshot_id: int,
        status: str,
    ) -> VersionSnapshot:
        snapshot = self.session.get(
            VersionSnapshot,
            snapshot_id,
        )

        if snapshot is None:
            raise ValueError("Snapshot does not exist.")

        snapshot.status = status
        if status == "ready":
            snapshot.ready_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot


    # ========================================================
    # DELETE VERSION
    # ========================================================

    def delete_version(
        self,
        version_id: int,
    ) -> bool:
        """
        Delete a document version from the database.

        Note:
            This only removes the database record.

        Physical storage and MySQL chunk cleanup should be handled
        by their respective layers.
        """

        version = self.session.get(
            DocumentVersion,
            version_id,
        )

        if version is None:

            return False

        self.session.delete(
            version
        )

        self.session.commit()

        return True

    # ========================================================
    # ROLE-BASED ACCESS CONTROL (RBAC)
    # ========================================================

    def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        can_access_all: bool = False,
        is_active: bool = True,
    ) -> Role:
        normalized_name = name.strip().lower()
        role = Role(
            name=normalized_name,
            description=description,
            can_access_all=can_access_all,
            is_active=is_active,
        )
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def get_role(
        self,
        name: str,
    ) -> Optional[Role]:
        normalized_name = name.strip().lower()
        statement = select(Role).where(Role.name == normalized_name)
        return self.session.scalar(statement)

    def list_roles(self) -> list[Role]:
        statement = select(Role).order_by(Role.name)
        return list(self.session.scalars(statement).all())

    def delete_role(self, name: str) -> bool:
        role = self.get_role(name)
        if role is None:
            return False
        self.session.delete(role)
        self.session.commit()
        return True

    def deactivate_role(self, name: str) -> bool:
        role = self.get_role(name)
        if role is None:
            return False
        role.is_active = False
        self.session.commit()
        self.session.refresh(role)
        return True

    def set_role_access_all(self, name: str, can_access_all: bool) -> bool:
        role = self.get_role(name)
        if role is None:
            return False
        role.can_access_all = can_access_all
        self.session.commit()
        self.session.refresh(role)
        return True

    def grant_document_access(
        self,
        role_name: str,
        document_identifier: str,
        documentation_version: Optional[str] = None,
    ) -> RoleDocumentAccess:
        role = self.get_role(role_name)
        if role is None:
            raise ValueError(f"Role '{role_name}' does not exist.")

        norm_doc = document_identifier.strip().lower()
        if norm_doc.endswith(".md"):
            norm_doc = norm_doc[:-3]

        norm_ver = str(documentation_version).strip() if documentation_version is not None else None

        # Check if already granted
        for existing in role.document_access:
            existing_ver = str(existing.documentation_version).strip() if existing.documentation_version is not None else None
            if existing.document_identifier.lower() == norm_doc and existing_ver == norm_ver:
                return existing

        grant = RoleDocumentAccess(
            role_id=role.id,
            document_identifier=norm_doc,
            documentation_version=norm_ver,
        )
        self.session.add(grant)
        self.session.commit()
        self.session.refresh(grant)
        return grant

    def revoke_document_access(
        self,
        role_name: str,
        document_identifier: str,
        documentation_version: Optional[str] = None,
    ) -> bool:
        role = self.get_role(role_name)
        if role is None:
            return False

        norm_doc = document_identifier.strip().lower()
        if norm_doc.endswith(".md"):
            norm_doc = norm_doc[:-3]

        norm_ver = str(documentation_version).strip() if documentation_version is not None else None

        found = False
        for grant in list(role.document_access):
            existing_ver = str(grant.documentation_version).strip() if grant.documentation_version is not None else None
            if grant.document_identifier.lower() == norm_doc and existing_ver == norm_ver:
                self.session.delete(grant)
                found = True

        if found:
            self.session.commit()
        return found

    def list_all_document_identifiers(self) -> list[str]:
        """Return all distinct ingested document identifiers (file stems)."""
        statement = select(DocumentVersion.file_name).distinct()
        raw_names = self.session.scalars(statement).all()
        identifiers = {
            Path(name).stem.lower()
            for name in raw_names
            if name
        }
        return sorted(list(identifiers))

    def get_snapshot_document_versions(
        self,
        snapshot_id: int,
    ) -> list[tuple[int, str]]:
        """Return list of (document_version_id, document_identifier_stem) for a snapshot."""
        statement = (
            select(SnapshotDocument.document_version_id, DocumentVersion.file_name)
            .join(DocumentVersion, DocumentVersion.id == SnapshotDocument.document_version_id)
            .where(SnapshotDocument.snapshot_id == snapshot_id)
        )
        rows = self.session.execute(statement).all()
        return [
            (row[0], Path(row[1]).stem.lower())
            for row in rows
            if row[1]
        ]

    def get_role_allowed_document_version_ids(
        self,
        role_name: str,
        snapshot_id: int,
        documentation_version: Optional[str] = None,
    ) -> list[int]:
        role = self.get_role(role_name)
        if role is None or not role.is_active:
            return []

        doc_versions = self.get_snapshot_document_versions(snapshot_id)
        if role.can_access_all:
            return [vid for vid, _ in doc_versions]

        ver_str = str(documentation_version).strip() if documentation_version is not None else None
        allowed_stems = {
            grant.document_identifier.lower()
            for grant in role.document_access
            if grant.documentation_version is None or str(grant.documentation_version).strip() == ver_str
        }

        return [
            vid
            for vid, stem in doc_versions
            if stem in allowed_stems
        ]