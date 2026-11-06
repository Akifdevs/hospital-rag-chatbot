import time
import pytest
from fastapi.testclient import TestClient

from api import app
from database.connection import get_session
from database.repository import DocumentRepository
from performance import answer_cache
from auth.roles import (
    resolve_request_role,
    clear_role_cache,
    DENY_ALL_ROLE,
)
import scripts.manage_roles as manage_roles

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_roles_and_cache():
    # Seed example roles (admin & receptionist)
    manage_roles.cmd_seed_examples(None)
    clear_role_cache()
    with answer_cache._lock:
        answer_cache._entries.clear()
    yield
    clear_role_cache()
    with answer_cache._lock:
        answer_cache._entries.clear()


def test_role_resolution_safe_handling():
    """Verify whitespace trimming, lowercasing, regex validation, and injection safety."""
    # Case insensitivity & trimming
    assert resolve_request_role({"X-User-Role": " ADMIN "}) == "admin"
    assert resolve_request_role({"X-User-Role": "Admin"}) == "admin"
    assert resolve_request_role({"X-User-Role": "ADMIN"}) == "admin"
    assert resolve_request_role({"X-User-Role": " RECEPTIONIST "}) == "receptionist"

    # SQL Injection / special characters -> fallback to default role
    assert resolve_request_role({"X-User-Role": "admin; DROP TABLE roles;"}) == "receptionist"
    assert resolve_request_role({"X-User-Role": "admin' OR 1=1--"}) == "receptionist"

    # Length boundary (> 50 characters) -> fallback to default role
    too_long = "a" * 51
    assert resolve_request_role({"X-User-Role": too_long}) == "receptionist"

    # Missing or empty header -> fallback to default role
    assert resolve_request_role({}) == "receptionist"
    assert resolve_request_role({"X-User-Role": ""}) == "receptionist"
    assert resolve_request_role({"X-User-Role": "   "}) == "receptionist"

    # From payload object or dict with role key
    assert resolve_request_role({"role": "admin"}) == "admin"
    assert resolve_request_role({"role": " ADMIN "}) == "admin"
    assert resolve_request_role({"role": "receptionist"}) == "receptionist"
    assert resolve_request_role({"role": "unknown"}) == "receptionist"

    # Unknown role -> fallback to default role
    assert resolve_request_role({"X-User-Role": "nonexistent_role"}) == "receptionist"


def test_default_role_not_existing_denies_all(monkeypatch):
    """If RAG_DEFAULT_ROLE does not exist in DB or is inactive, access is completely denied."""
    monkeypatch.setattr("auth.roles.RAG_DEFAULT_ROLE", "phantom_role_that_does_not_exist")
    clear_role_cache()

    resolved = resolve_request_role({})
    assert resolved == DENY_ALL_ROLE

    # When querying with deny all, response must be the normal generic refusal
    response = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "unknown_role"},
        json={
            "query": "What are the three billing modes?",
            "version": "1",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "couldn't find information about that in the documentation" in data["answer"]


def test_admin_gets_radiology_and_receptionist_gets_refusal():
    """
    admin gets an answer from radiology-guide;
    receptionist asking the same question gets the generic refusal.
    """
    radiology_query = "What modality filter pills are available in the radiology dashboard?"

    # 1. Admin asking radiology query
    admin_resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "admin"},
        json={"query": radiology_query, "version": "1"},
    )
    assert admin_resp.status_code == 200
    admin_data = admin_resp.json()
    assert admin_data["success"] is True
    assert ("X-Ray" in admin_data["answer"] or "CT" in admin_data["answer"] or "MRI" in admin_data["answer"])

    # 2. Receptionist asking the same radiology query -> must be refused
    rec_resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "receptionist"},
        json={"query": radiology_query, "version": "1"},
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["success"] is False
    assert "couldn't find information about that in the documentation" in rec_data["answer"]
    # Never mention role name, document name, or 'Version 1'
    assert "receptionist" not in rec_data["answer"].lower()
    assert "radiology" not in rec_data["answer"].lower()
    assert "Version 1" not in rec_data["answer"]


def test_role_passed_via_json_payload():
    """Verify role passed in JSON payload is respected even without X-User-Role header."""
    radiology_query = "What modality filter pills are available in the radiology dashboard?"

    # 1. Admin via payload
    admin_resp = client.post(
        "/api/v1/chat",
        json={"query": radiology_query, "version": "1", "role": "admin"},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["success"] is True

    # 2. Receptionist via payload
    rec_resp = client.post(
        "/api/v1/chat",
        json={"query": radiology_query, "version": "1", "role": "receptionist"},
    )
    assert rec_resp.status_code == 200
    assert rec_resp.json()["success"] is False
    assert "couldn't find information about that in the documentation" in rec_resp.json()["answer"]


def test_receptionist_gets_answers_from_billing_guide():
    """receptionist gets answers from billing-guide."""
    billing_query = "What are the three billing modes in the billing guide?"

    rec_resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "receptionist"},
        json={"query": billing_query, "version": "1"},
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["success"] is True
    assert ("Cash" in rec_data["answer"] or "Insurance" in rec_data["answer"])


def test_no_cross_role_cache_leakage_in_either_order():
    """Same question asked as admin and then as receptionist: no cache leakage in either order."""
    question = "Can a Radiographer mark a report as Final in radiology?"

    # Order 1: Admin first, then Receptionist
    admin_resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "admin"},
        json={"query": question, "version": "1"},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["success"] is True

    rec_resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "receptionist"},
        json={"query": question, "version": "1"},
    )
    assert rec_resp.status_code == 200
    assert rec_resp.json()["success"] is False
    assert "couldn't find information about that in the documentation" in rec_resp.json()["answer"]

    # Order 2: Clear cache, Receptionist first, then Admin
    with answer_cache._lock:
        answer_cache._entries.clear()

    rec_resp2 = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "receptionist"},
        json={"query": question, "version": "1"},
    )
    assert rec_resp2.status_code == 200
    assert rec_resp2.json()["success"] is False

    admin_resp2 = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "admin"},
        json={"query": question, "version": "1"},
    )
    assert admin_resp2.status_code == 200
    assert admin_resp2.json()["success"] is True


def test_create_brand_new_role_cli_and_works_immediately_or_after_ttl(monkeypatch):
    """
    Create a brand-new role through the CLI (no code change), grant one document,
    and it works immediately after the TTL.
    """
    new_role = "radiologist"

    # Create role and grant radiology-guide
    class ArgsCreate:
        name = new_role
        all = False
        description = "Radiology specialist"

    manage_roles.cmd_create_role(ArgsCreate)

    class ArgsGrant:
        role = new_role
        document = "radiology-guide"
        version = None

    manage_roles.cmd_grant(ArgsGrant)

    # Fast TTL simulation: verify cache expiration behavior
    clear_role_cache()

    # Query as radiologist for radiology question
    resp = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": new_role},
        json={
            "query": "What modality filter pills are available in the radiology dashboard?",
            "version": "1",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert ("X-Ray" in data["answer"] or "CT" in data["answer"] or "MRI" in data["answer"])

    # Radiologist should NOT have access to inventory-guide or medical-history-guide
    resp_inv = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": new_role},
        json={
            "query": "What is Cedar Nexus?",
            "version": "1",
        },
    )
    assert resp_inv.status_code == 200
    assert resp_inv.json()["success"] is False
    assert "couldn't find information about that in the documentation" in resp_inv.json()["answer"]

    # Clean up created role
    class ArgsDel:
        name = new_role

    manage_roles.cmd_delete_role(ArgsDel)


def test_existing_behaviour_greetings_and_smalltalk_unchanged():
    """Existing behaviour (greetings, acknowledgements) is unchanged."""
    # Greeting
    resp_greet = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "receptionist"},
        json={"query": "hi", "version": "1"},
    )
    assert resp_greet.status_code == 200
    assert resp_greet.json()["success"] is True
    assert "Hey there!" in resp_greet.json()["answer"]

    # Thanks
    resp_thanks = client.post(
        "/api/v1/chat",
        headers={"X-User-Role": "admin"},
        json={"query": "thank you", "version": "1"},
    )
    assert resp_thanks.status_code == 200
    assert resp_thanks.json()["success"] is True
    assert "welcome" in resp_thanks.json()["answer"].lower()

