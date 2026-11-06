from pathlib import Path
import time

from ingestion.watcher import SourceSetWatcher


def test_watcher_scans_source_sets_without_generated_revision_directories(tmp_path):
    source_root = tmp_path / "documents"
    source_set = source_root / "version alpha"
    source_set.mkdir(parents=True)
    (source_set / "service.md").write_text("v1", encoding="utf-8")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )

    state = watcher._scan()

    assert str(source_set.resolve()) in state
    assert str((source_root / "1").resolve()) not in state


def test_watcher_detects_file_changes_in_source_set(tmp_path):
    source_root = tmp_path / "documents"
    source_set = source_root / "version alpha"
    source_set.mkdir(parents=True)
    source_file = source_set / "service.md"
    source_file.write_text("v1", encoding="utf-8")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )

    before = watcher._scan()
    source_file.write_text("v2", encoding="utf-8")
    after = watcher._scan()

    assert before != after
    assert str(source_set.resolve()) in after


def _create_initial_docs(source_set: Path, v_label: str = "v1"):
    source_set.mkdir(parents=True, exist_ok=True)
    (source_set / "service-order-rag.md").write_text(
        f"service content {v_label}", encoding="utf-8"
    )
    (source_set / "billing-payments-rag.md").write_text(
        f"billing content {v_label}", encoding="utf-8"
    )
    (source_set / "appointment-scheduling-rag.md").write_text(
        f"appointment content {v_label}", encoding="utf-8"
    )


def test_editing_version_1_detected_by_poll_once(tmp_path):
    source_root = tmp_path / "documents"
    v1 = source_root / "version 1"
    _create_initial_docs(v1, "v1")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )
    watcher._state = watcher._scan()

    # Edit service-order-rag.md in version 1
    (v1 / "service-order-rag.md").write_text(
        "service content v1 EDITED", encoding="utf-8"
    )

    changed = watcher.poll_once()

    assert len(changed) == 1
    assert changed[0].resolve() == v1.resolve()


def test_subsequent_poll_without_changes_returns_empty(tmp_path):
    source_root = tmp_path / "documents"
    v1 = source_root / "version 1"
    _create_initial_docs(v1, "v1")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )
    watcher._state = watcher._scan()

    # Edit service-order-rag.md in version 1
    (v1 / "service-order-rag.md").write_text(
        "service content v1 EDITED", encoding="utf-8"
    )

    changed = watcher.poll_once()
    assert len(changed) == 1

    # Next poll cycle MUST NOT report the folder again without new changes
    changed_next = watcher.poll_once()
    assert changed_next == []


def test_saving_unchanged_content_does_not_trigger_change(tmp_path):
    source_root = tmp_path / "documents"
    v1 = source_root / "version 1"
    _create_initial_docs(v1, "v1")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )
    watcher._state = watcher._scan()

    # Re-save identical content
    current_content = (v1 / "service-order-rag.md").read_text(encoding="utf-8")
    (v1 / "service-order-rag.md").write_text(current_content, encoding="utf-8")

    changed = watcher.poll_once()
    assert changed == []


def test_nonexistent_source_root_returns_empty(tmp_path):
    source_root = tmp_path / "does_not_exist"
    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
    )
    assert watcher._source_sets() == []
    assert watcher._scan() == {}
    assert watcher.poll_once() == []


def test_watcher_lifecycle(tmp_path):
    source_root = tmp_path / "documents"
    v1 = source_root / "version 1"
    _create_initial_docs(v1, "v1")

    watcher = SourceSetWatcher(
        source_root=source_root,
        source_set_glob="version *",
        interval_seconds=0.1,
    )
    watcher.start()
    assert watcher._thread is not None
    assert watcher._thread.is_alive()

    watcher.stop()
    assert watcher._thread is None
