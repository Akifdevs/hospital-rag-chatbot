from retrieval.retrieval import build_snapshot_filter


def test_snapshot_filter_contains_only_attached_document_versions():
    snapshot_filter = build_snapshot_filter([11, 22, 33])

    assert len(snapshot_filter.must) == 1
    condition = snapshot_filter.must[0]
    assert condition.key == "document_version_id"
    assert condition.match.any == [11, 22, 33]
