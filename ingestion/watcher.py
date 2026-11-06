"""
ingestion/watcher.py
====================

Content-hash-aware source watcher.

IMPORTANT:

This watcher is DETECTION ONLY.

It does NOT:
    - ingest documents
    - create DocumentVersion rows
    - create VersionSnapshot rows
    - determine global versions
    - publish versions

Global versions are created ONLY when the developer explicitly runs:

    python register_and_ingest_documents.py <source-directory>

The watcher exists only to report source-file changes.
"""

import hashlib
import logging
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(
    "strict-rag-watcher"
)


def calculate_file_sha256(
    file_path: Path,
) -> str:
    """
    Calculate SHA-256 for a file.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        for block in iter(
            lambda: file.read(65536),
            b"",
        ):
            sha256.update(block)

    return sha256.hexdigest()


class SourceSetWatcher:
    """
    Detect content changes in document source folders.

    The watcher deliberately has no ingestion callback.
    """

    def __init__(
        self,
        source_root: Path,
        source_set_glob: str,
        interval_seconds: float = 2.0,
        debounce_seconds: float = 1.0,
    ):
        self.source_root = (
            Path(source_root).resolve()
        )

        self.source_set_glob = (
            source_set_glob
        )

        self.interval_seconds = (
            interval_seconds
        )

        self.debounce_seconds = (
            debounce_seconds
        )

        self._stop_event = (
            threading.Event()
        )

        self._thread: Optional[
            threading.Thread
        ] = None

        # {
        #     "/path/to/version 1": {
        #         "file.md": "sha256..."
        #     }
        # }
        self._state: dict[
            str,
            dict[str, str],
        ] = {}

    # ========================================================
    # SOURCE DISCOVERY
    # ========================================================

    def _source_sets(self) -> list[Path]:
        """
        Return watched source directories.
        """

        if not self.source_root.exists():
            return []

        direct_files = [
            file
            for file in self.source_root.glob(
                "*.md"
            )
            if file.is_file()
        ]

        subfolders = sorted(
            path
            for path in self.source_root.glob(
                self.source_set_glob
            )
            if path.is_dir()
        )

        if subfolders:
            return subfolders

        if direct_files:
            return [
                self.source_root
            ]

        return []

    # ========================================================
    # HASH SCANNING
    # ========================================================

    def _scan(
        self,
    ) -> dict[str, dict[str, str]]:
        """
        Scan watched folders and calculate file hashes.
        """

        state: dict[
            str,
            dict[str, str],
        ] = {}

        for source_set in self._source_sets():

            files: dict[str, str] = {}

            for path in sorted(
                source_set.rglob("*")
            ):

                if not path.is_file():
                    continue

                if path.name.startswith(
                    (".", "~", "#")
                ):
                    continue

                if path.suffix.lower() in {
                    ".tmp",
                    ".swp",
                }:
                    continue

                try:

                    file_hash = (
                        calculate_file_sha256(
                            path
                        )
                    )

                    relative_path = str(
                        path.relative_to(
                            source_set
                        )
                    )

                    files[
                        relative_path
                    ] = file_hash

                except (
                    FileNotFoundError,
                    PermissionError,
                ):
                    continue

            state[
                str(source_set.resolve())
            ] = files

        return state

    # ========================================================
    # CHANGE DETECTION
    # ========================================================

    def poll_once(
        self,
    ) -> list[Path]:
        """
        Detect source changes.

        Returns the folders that changed.

        NO ingestion happens here.
        """

        current_state = self._scan()

        if current_state == self._state:
            return []

        all_folders = sorted(
            set(self._state.keys())
            | set(current_state.keys())
        )

        changed_folders: list[Path] = []

        for folder_str in all_folders:

            previous_files = (
                self._state.get(
                    folder_str,
                    {},
                )
            )

            current_files = (
                current_state.get(
                    folder_str,
                    {},
                )
            )

            if previous_files != current_files:

                changed_folders.append(
                    Path(folder_str)
                )

                modified = [
                    path
                    for path, file_hash
                    in current_files.items()
                    if (
                        path in previous_files
                        and previous_files[path]
                        != file_hash
                    )
                ]

                added = [
                    path
                    for path in current_files
                    if path not in previous_files
                ]

                removed = [
                    path
                    for path in previous_files
                    if path not in current_files
                ]

                logger.info(
                    "Source change detected | "
                    "folder=%s | modified=%s | "
                    "added=%s | removed=%s | "
                    "manual ingestion required",
                    Path(folder_str).name,
                    modified,
                    added,
                    removed,
                )

        self._state = current_state

        return changed_folders

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def start(self) -> None:
        """
        Start the detection watcher.

        Startup only establishes the current disk state.

        It does NOT compare against the database and does NOT
        trigger ingestion for changes that happened while the
        application was offline.
        """

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        # Seed from CURRENT DISK STATE.
        #
        # This is critical:
        # starting the backend must never turn existing filesystem
        # differences into a new global version.
        self._state = self._scan()

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="rag-source-watcher",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Source watcher started | "
            "root=%s | glob=%s | "
            "mode=detection-only",
            self.source_root,
            self.source_set_glob,
        )

    def stop(self) -> None:
        """
        Stop the watcher.
        """

        self._stop_event.set()

        if self._thread is not None:

            self._thread.join(
                timeout=max(
                    self.interval_seconds + 1,
                    3,
                )
            )

        self._thread = None

        logger.info(
            "Source watcher stopped"
        )

    # ========================================================
    # BACKGROUND LOOP
    # ========================================================

    def _run(self) -> None:

        pending_since: Optional[
            float
        ] = None

        pending_state = self._state

        while not self._stop_event.wait(
            self.interval_seconds
        ):

            current_state = self._scan()

            if current_state == self._state:

                pending_since = None

                continue

            if pending_since is None:

                pending_since = (
                    time.monotonic()
                )

                pending_state = (
                    current_state
                )

                continue

            if current_state != pending_state:

                pending_state = (
                    current_state
                )

                pending_since = (
                    time.monotonic()
                )

                continue

            if (
                time.monotonic()
                - pending_since
                < self.debounce_seconds
            ):
                continue

            self.poll_once()

            pending_state = self._state

            pending_since = None


# ============================================================
# STANDALONE WATCHER
# ============================================================

if __name__ == "__main__":

    from performance import (
        RAG_INGEST_WATCH_ROOT,
        RAG_INGEST_SOURCE_SET_GLOB,
        RAG_INGEST_WATCH_INTERVAL_SECONDS,
        RAG_INGEST_DEBOUNCE_SECONDS,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(message)s"
        ),
    )

    root = Path(
        RAG_INGEST_WATCH_ROOT
    )

    if not root.is_absolute():

        root = (
            Path(__file__).resolve().parent.parent
            / root
        )

    watcher = SourceSetWatcher(
        source_root=root,
        source_set_glob=(
            RAG_INGEST_SOURCE_SET_GLOB
        ),
        interval_seconds=(
            RAG_INGEST_WATCH_INTERVAL_SECONDS
        ),
        debounce_seconds=(
            RAG_INGEST_DEBOUNCE_SECONDS
        ),
    )

    watcher.start()

    print(
        f"\nWatching: {root}"
    )

    print(
        "Mode: detection only"
    )

    print(
        "Run register_and_ingest_documents.py "
        "manually to create a new version."
    )

    print(
        "\nPress Ctrl+C to stop.\n"
    )

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        watcher.stop()