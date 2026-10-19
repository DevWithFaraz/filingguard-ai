"""Integration tests for finding collaboration, reviewer roles, and sign-off."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from filingguard.core.config import Settings
from filingguard.db.models import Base, Finding
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.main import create_app

ORIGIN = "http://localhost:5173"


@pytest.fixture
def test_client(tmp_path, monkeypatch):
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


def submit(client, auth, name="Motion to Dismiss"):
    res = client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": name,
            "text": "First paragraph.\n\nSecond paragraph.",
            "court_profile_id": "unverified",
            "ai_used": False,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["analysis_id"]


def add_finding_to_analysis(factory, analysis_id):
    finding_id = uuid4()
    with factory() as session:
        finding = Finding(
            id=finding_id,
            analysis_id=UUID(analysis_id),
            type="quote",
            severity="medium",
            title="Quotation discrepancy",
            description="Quote differs from source text.",
            status="open",
            stage="quotes",
            ai_assisted=False,
        )
        session.add(finding)
        session.commit()
    return finding_id


def test_add_and_list_finding_comments(test_client):
    client, factory = test_client
    auth = headers(client)

    aid = submit(client, auth)
    fid = add_finding_to_analysis(factory, aid)

    # Add first comment
    comment_res = client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/comments",
        headers=auth,
        json={
            "author_name": "Attorney Alice",
            "author_role": "lead_attorney",
            "content": "Verified against official reporter; harmless typo.",
        },
    )
    assert comment_res.status_code == 201, comment_res.text
    c1 = comment_res.json()
    assert c1["author_name"] == "Attorney Alice"
    assert c1["author_role"] == "lead_attorney"
    assert "harmless typo" in c1["content"]

    # Add second comment
    comment_res2 = client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/comments",
        headers=auth,
        json={
            "author_name": "Paralegal Bob",
            "author_role": "paralegal",
            "content": "Added pincite page reference.",
        },
    )
    assert comment_res2.status_code == 201

    # List comments
    list_res = client.get(f"/api/v1/analyses/{aid}/findings/{fid}/comments", headers=auth)
    assert list_res.status_code == 200
    comments = list_res.json()
    assert len(comments) == 2
    assert comments[0]["author_name"] == "Attorney Alice"
    assert comments[1]["author_name"] == "Paralegal Bob"


def test_set_finding_disposition_signoff(test_client):
    client, factory = test_client
    auth = headers(client)

    aid = submit(client, auth)
    fid = add_finding_to_analysis(factory, aid)

    # Set disposition to accepted
    disp_res = client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/disposition",
        headers=auth,
        json={
            "status": "accepted",
            "rationale": "Citation quotation confirmed accurate after replacement.",
            "reviewer_name": "Partner Jane",
            "reviewer_role": "lead_attorney",
        },
    )
    assert disp_res.status_code == 200, disp_res.text
    disp = disp_res.json()
    assert disp["status"] == "accepted"
    assert disp["disposition_metadata"]["reviewer_name"] == "Partner Jane"
    assert disp["disposition_metadata"]["status"] == "accepted"
    assert len(disp["disposition_metadata"]["history"]) == 1

    # Update disposition to dismissed with another reason
    disp_res2 = client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/disposition",
        headers=auth,
        json={
            "status": "dismissed",
            "rationale": "Non-material difference in footnote text.",
            "reviewer_name": "Associate Dan",
            "reviewer_role": "associate_reviewer",
        },
    )
    assert disp_res2.status_code == 200
    disp2 = disp_res2.json()
    assert disp2["status"] == "dismissed"
    assert len(disp2["disposition_metadata"]["history"]) == 2


def test_collaboration_owner_isolation(test_client):
    client, factory = test_client
    owner_a = headers(client)
    owner_b = headers(client)

    aid = submit(client, owner_a)
    fid = add_finding_to_analysis(factory, aid)

    # Owner B cannot view or add comments
    assert client.get(
        f"/api/v1/analyses/{aid}/findings/{fid}/comments", headers=owner_b
    ).status_code == 404
    assert client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/comments",
        headers=owner_b,
        json={"author_name": "B", "author_role": "paralegal", "content": "test"},
    ).status_code == 404

    # Owner B cannot update disposition
    assert client.post(
        f"/api/v1/analyses/{aid}/findings/{fid}/disposition",
        headers=owner_b,
        json={
            "status": "dismissed",
            "rationale": "not mine",
            "reviewer_name": "B",
            "reviewer_role": "paralegal",
        },
    ).status_code == 404
