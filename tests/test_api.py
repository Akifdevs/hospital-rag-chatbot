import pytest
from fastapi.testclient import TestClient

from api import ChatRequest, app
from performance import answer_cache


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    with answer_cache._lock:
        answer_cache._entries.clear()
    yield
    with answer_cache._lock:
        answer_cache._entries.clear()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_requires_query():
    response = client.post(
        "/api/v1/chat",
        json={"version": 1},
    )
    assert response.status_code == 422


def test_chat_request_accepts_widget_host_page_url():
    request = ChatRequest(
        query="How do I create a package?",
        version=1,
        url="https://host-application.example/orders/123",
    )

    assert request.url == "https://host-application.example/orders/123"


def test_chat_rejects_legacy_document_payload():
    response = client.post(
        "/api/v1/chat",
        json={
            "question": "How do I create a package?",
            "document_id": 1,
        },
    )
    assert response.status_code == 422


def test_chat_no_version_returns_version_required(monkeypatch):
    class FakeSnapshot1:
        version_number = 1

    class FakeSnapshot2:
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def list_snapshots(self, ready_only=False):
            assert ready_only is True
            return [FakeSnapshot1(), FakeSnapshot2()]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_question should NOT be called when no version is provided")

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fail_if_called)

    response = client.post(
        "/api/v1/chat",
        json={"query": "How do I create a package?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "version_required"
    assert "Version 1" in data["answer"]
    assert "Version 2" in data["answer"]


def test_chat_nonexistent_version_returns_version_not_found(monkeypatch):
    class FakeSnapshot:
        version_number = 1

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert version == 99
            return None

        def list_snapshots(self, ready_only=False):
            assert ready_only is True
            return [FakeSnapshot()]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_question should NOT be called for non-existent version")

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fail_if_called)

    response = client.post(
        "/api/v1/chat",
        json={"query": "in version 99, how do I create a package?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "version_not_found"
    assert "Version 1" in data["answer"]


def test_chat_query_extracts_and_strips_valid_version(monkeypatch):
    class FakeSnapshot:
        id = 1
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert version == 2
            assert ready_only is True
            return FakeSnapshot()

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [10, 20]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    called_kwargs = {}

    def fake_answer_question(query, version, snapshot_data, history):
        called_kwargs["query"] = query
        called_kwargs["version"] = version
        return {
            "success": True,
            "answer": "Package creation workflow.",
            "sources": [],
        }

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fake_answer_question)

    response = client.post(
        "/api/v1/chat",
        json={"query": "i want answer from version 2\nhow do I create a package?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["answer"] == "Package creation workflow."
    assert called_kwargs["version"] == 2
    assert called_kwargs["query"] == "how do I create a package?"


def test_chat_version_without_question_returns_friendly_prompt(monkeypatch):
    class FakeSnapshot:
        id = 1
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            return FakeSnapshot()

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [10, 20]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_question should NOT be called when no question is present")

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fail_if_called)

    response = client.post(
        "/api/v1/chat",
        json={"query": "version 2"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "question" in data["answer"].lower()


def test_chat_answer_not_available_in_version_fallback(monkeypatch):
    class FakeSnapshot:
        id = 1
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            return FakeSnapshot()

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [10, 20]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fake_answer_question(query, version, snapshot_data, history):
        return {
            "success": False,
            "answer": (
                f"I couldn't find information about that in Version {version}. "
                "It may be covered in a different version — let me know if you'd like to try another version."
            ),
            "sources": [],
        }

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fake_answer_question)

    response = client.post(
        "/api/v1/chat",
        json={"query": "in version 2, how do I delete a package?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "I couldn't find information about that in Version 2" in data["answer"]
    assert "different version" in data["answer"]


def test_chat_explicit_request_version_priority_and_backward_compatibility(monkeypatch):
    class FakeSnapshot:
        id = 1
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert version == 2
            assert ready_only is True
            return FakeSnapshot()

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [11, 22]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    called_kwargs = {}

    def fake_answer_question(query, version, snapshot_data, history):
        called_kwargs["version"] = version
        called_kwargs["query"] = query
        return {
            "success": True,
            "answer": "Use the package workflow.",
            "sources": [],
        }

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fake_answer_question)

    # Both explicit request.version=2 and in-text 'version 1' are present; request.version takes priority
    response = client.post(
        "/api/v1/chat",
        json={
            "version": 2,
            "query": "in version 1, how do I create a package?",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert called_kwargs["version"] == 2
    assert called_kwargs["query"] == "how do I create a package?"


def test_chat_sticky_version_from_history(monkeypatch):
    class FakeSnapshot:
        id = 1
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert version == 2
            assert ready_only is True
            return FakeSnapshot()

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [10, 20]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    called_kwargs = {}

    def fake_answer_question(query, version, snapshot_data, history):
        called_kwargs["version"] = version
        called_kwargs["query"] = query
        return {
            "success": True,
            "answer": "Follow-up answer.",
            "sources": [],
        }

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fake_answer_question)

    # Message 2 in the conversation sends message 1 in history. Message 2 omits version.
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "how do I cancel it?",
            "history": [
                {
                    "question": "in version 2, how do I create a package?",
                    "answer": "Package creation workflow.",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["answer"] == "Follow-up answer."
    assert called_kwargs["version"] == 2
    assert called_kwargs["query"] == "how do I cancel it?"


def test_chat_sticky_version_override_and_persistence(monkeypatch):
    class FakeSnapshot1:
        id = 1
        version_number = 1

    class FakeSnapshot2:
        id = 2
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert ready_only is True
            if version == 1:
                return FakeSnapshot1()
            if version == 2:
                return FakeSnapshot2()
            return None

        def get_snapshot_document_version_ids(self, snapshot_id):
            return [10, 20]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    called_kwargs = {}

    def fake_answer_question(query, version, snapshot_data, history):
        called_kwargs["version"] = version
        called_kwargs["query"] = query
        return {
            "success": True,
            "answer": f"Answer for version {version}.",
            "sources": [],
        }

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fake_answer_question)

    # Message 2 explicitly specifies version 2 while history had version 1 -> uses version 2
    resp2 = client.post(
        "/api/v1/chat",
        json={
            "query": "now in version 2, how do I delete a package?",
            "history": [
                {
                    "question": "in version 1, how do I create a package?",
                    "answer": "Answer for version 1.",
                }
            ],
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True
    assert called_kwargs["version"] == 2
    assert called_kwargs["query"] == "how do I delete a package?"

    # Message 3 omits version -> should stick to version 2, not version 1
    resp3 = client.post(
        "/api/v1/chat",
        json={
            "query": "what payment methods are supported?",
            "history": [
                {
                    "question": "in version 1, how do I create a package?",
                    "answer": "Answer for version 1.",
                },
                {
                    "question": "now in version 2, how do I delete a package?",
                    "answer": "Answer for version 2.",
                },
            ],
        },
    )
    assert resp3.status_code == 200
    assert resp3.json()["success"] is True
    assert called_kwargs["version"] == 2
    assert called_kwargs["query"] == "what payment methods are supported?"


def test_chat_no_version_in_history_returns_version_required(monkeypatch):
    class FakeSnapshot1:
        version_number = 1

    class FakeSnapshot2:
        version_number = 2

    class FakeRepository:
        def __init__(self, session):
            pass

        def list_snapshots(self, ready_only=False):
            assert ready_only is True
            return [FakeSnapshot1(), FakeSnapshot2()]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_question should NOT be called when no version was ever provided")

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fail_if_called)

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "can two patients be booked?",
            "history": [
                {
                    "question": "how do I create a package?",
                    "answer": "Please specify which version of the documentation you'd like me to answer from.",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "version_required"
    assert "Version 1" in data["answer"]
    assert "Version 2" in data["answer"]


def test_chat_sticky_version_no_longer_exists(monkeypatch):
    class FakeSnapshot:
        version_number = 1

    class FakeRepository:
        def __init__(self, session):
            pass

        def get_snapshot(self, version, ready_only=False):
            assert version == 2
            # Version 2 is no longer available/ready
            return None

        def list_snapshots(self, ready_only=False):
            assert ready_only is True
            return [FakeSnapshot()]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_question should NOT be called when sticky version is missing")

    monkeypatch.setattr("api.get_session", lambda: FakeSession())
    monkeypatch.setattr("api.DocumentRepository", FakeRepository)
    monkeypatch.setattr("api.answer_question", fail_if_called)

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "how do I delete it?",
            "history": [
                {
                    "question": "in version 2, how do I create a package?",
                    "answer": "Package creation workflow.",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "version_not_found"
    assert "Version 1" in data["answer"]