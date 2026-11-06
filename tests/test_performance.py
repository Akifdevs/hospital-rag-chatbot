from performance import VersionedAnswerCache
from retrieval.retrieval import build_snapshot_filter


def test_answer_cache_isolated_by_global_version():
    cache = VersionedAnswerCache(max_entries=4, ttl_seconds=60)
    cache.set(1, "  Appointment   booking? ", {"answer": "v1"})
    cache.set(2, "appointment booking?", {"answer": "v2"})

    assert cache.get(1, "appointment booking?") == {"answer": "v1"}
    assert cache.get(2, "appointment booking?") == {"answer": "v2"}


def test_snapshot_filter_remains_version_scoped_with_small_top_k():
    snapshot_filter = build_snapshot_filter([101, 202])

    assert snapshot_filter.must[0].key == "document_version_id"
    assert snapshot_filter.must[0].match.any == [101, 202]
