from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from filingguard.core.config import Settings
from filingguard.db.models import Base, IdentitySession
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.main import create_app

ORIGIN = "http://localhost:5173"
SECRET = "local-secret-12"
OTHER_SECRET = "other-secret-12"


@pytest.fixture
def private_client(tmp_path, monkeypatch):
    settings = Settings(intake_enabled=True, private_storage_directory=tmp_path / "private")
    monkeypatch.setattr("filingguard.main.Settings", lambda: settings)
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    with TestClient(create_app()) as client:
        yield client, create_session_factory(engine)


def headers(client):
    response = client.post("/api/v1/sessions", headers={"Origin": ORIGIN})
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["token"], "Origin": ORIGIN}


def submit(client, auth, text="Synthetic claim.\n\nSecond claim."):
    return client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": "Synthetic filing",
            "text": text,
            "court_profile_id": "unverified",
            "ai_used": True,
        },
    )


def claim(client, auth, username="reviewer_one", secret=SECRET):
    return client.post(
        "/api/v1/identities",
        headers=auth,
        json={"username": username, "secret": secret},
    )


def login(client, username="reviewer_one", secret=SECRET):
    return client.post(
        "/api/v1/identities/login",
        headers={"Origin": ORIGIN},
        json={"username": username, "secret": secret},
    )


def test_anonymous_tab_bearer_still_lists_without_claim(private_client):
    client, _ = private_client
    auth = headers(client)
    response = submit(client, auth)
    assert response.status_code == 201, response.text
    identity = response.json()["analysis_id"]
    listing = client.get("/api/v1/analyses", headers=auth)
    assert listing.status_code == 200
    assert listing.json()[0]["analysis_id"] == identity
    assert client.get("/api/v1/identities/me", headers=auth).status_code == 404
    assert client.get("/api/v1/analyses").status_code == 401
    unauthenticated = client.post(
        "/api/v1/identities", json={"username": "nobody", "secret": SECRET}
    )
    assert unauthenticated.status_code == 401


def test_claim_then_login_lists_own_analyses_only(private_client):
    client, _ = private_client
    owner = headers(client)
    other = headers(client)
    created = submit(client, owner)
    assert created.status_code == 201, created.text
    analysis_id = created.json()["analysis_id"]
    other_created = submit(client, other)
    assert other_created.status_code == 201, other_created.text
    other_id = other_created.json()["analysis_id"]

    claimed = claim(client, owner)
    assert claimed.status_code == 201, claimed.text
    assert claimed.json() == {"username": "reviewer_one", "bound": True}
    assert "secret" not in claimed.text
    assert client.get("/api/v1/identities/me", headers=owner).json()["username"] == "reviewer_one"

    recovered = login(client)
    assert recovered.status_code == 201, recovered.text
    recovered_auth = {
        "Authorization": "Bearer " + recovered.json()["token"],
        "Origin": ORIGIN,
    }
    listing = client.get("/api/v1/analyses", headers=recovered_auth)
    assert listing.status_code == 200
    ids = {row["analysis_id"] for row in listing.json()}
    assert ids == {analysis_id}
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=recovered_auth).status_code == 200
    assert client.get("/api/v1/analyses", headers=owner).json()[0]["analysis_id"] == analysis_id

    other_claim = claim(client, other, username="reviewer_two", secret=OTHER_SECRET)
    assert other_claim.status_code == 201, other_claim.text
    other_login = login(client, username="reviewer_two", secret=OTHER_SECRET)
    other_auth = {
        "Authorization": "Bearer " + other_login.json()["token"],
        "Origin": ORIGIN,
    }
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=other_auth).status_code == 404
    assert client.delete(f"/api/v1/analyses/{analysis_id}", headers=other_auth).status_code == 404
    other_listing = client.get("/api/v1/analyses", headers=other_auth).json()
    assert other_listing[0]["analysis_id"] == other_id
    assert analysis_id not in {row["analysis_id"] for row in other_listing}


def test_invalid_and_expired_identity_tokens_fail_closed(private_client):
    client, factory = private_client
    owner = headers(client)
    created = submit(client, owner)
    analysis_id = created.json()["analysis_id"]
    assert claim(client, owner).status_code == 201
    recovered = login(client)
    token = recovered.json()["token"]
    auth = {"Authorization": f"Bearer {token}", "Origin": ORIGIN}
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=auth).status_code == 200

    bogus = {"Authorization": "Bearer " + ("A" * 43), "Origin": ORIGIN}
    assert client.get("/api/v1/analyses", headers=bogus).status_code == 401
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=bogus).status_code == 401
    assert login(client, secret="wrong-secret-12").status_code == 401
    assert login(client, username="missing_user").status_code == 401
    assert client.post(
        "/api/v1/identities/login",
        json={"username": "reviewer_one", "secret": SECRET},
    ).status_code == 403

    with factory.begin() as session:
        session.execute(
            IdentitySession.__table__.update().values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
    assert client.get("/api/v1/analyses", headers=auth).status_code == 401
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=auth).status_code == 401
    assert client.get(f"/api/v1/analyses/{analysis_id}", headers=owner).status_code == 200


def test_duplicate_claim_conflicts_without_leaking_secret(private_client):
    client, _ = private_client
    first = headers(client)
    second = headers(client)
    assert claim(client, first).status_code == 201
    again = claim(client, first, username="reviewer_two", secret=OTHER_SECRET)
    assert again.status_code == 409
    taken = claim(client, second, username="reviewer_one", secret=OTHER_SECRET)
    assert taken.status_code == 409
    assert "local-secret" not in taken.text
    same = claim(client, first)
    assert same.status_code == 201


def test_migrate_anonymous_analyses_to_claimed_identity(private_client):
    client, _ = private_client
    primary_session = headers(client)
    claim_res = claim(client, primary_session, username="registered_user", secret=SECRET)
    assert claim_res.status_code == 201

    guest_session = headers(client)
    guest_created = submit(client, guest_session, text="Guest analysis content.")
    guest_analysis_id = guest_created.json()["analysis_id"]

    migrate_res = client.post(
        "/api/v1/identities/migrate",
        headers=guest_session,
        json={"username": "registered_user", "secret": SECRET},
    )
    assert migrate_res.status_code == 200, migrate_res.text
    data = migrate_res.json()
    assert data["migrated_count"] == 1
    new_token = data["session"]["token"]
    user_auth = {"Authorization": f"Bearer {new_token}", "Origin": ORIGIN}

    recovered = client.get(f"/api/v1/analyses/{guest_analysis_id}", headers=user_auth)
    assert recovered.status_code == 200
    assert recovered.json()["analysis_id"] == guest_analysis_id

    old_guest_check = client.get(f"/api/v1/analyses/{guest_analysis_id}", headers=guest_session)
    assert old_guest_check.status_code == 404

