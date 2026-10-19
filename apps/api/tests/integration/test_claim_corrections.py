from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from test_claims_pipeline import configure
from test_orchestrator import await_status, owner, prepare
from test_orchestrator import private_client as private_client

from filingguard.db.models import Analysis, Claim, ClaimAuthorityLink, Finding


def _correct(client, auth, analysis_id, claim_id, text):
    return client.post(
        f"/api/v1/analyses/{analysis_id}/claims/{claim_id}/corrections",
        headers=auth,
        json={"corrected_text": text},
    )


def test_owner_can_correct_claim_without_rewriting_original(private_client):
    client = private_client
    configure(client)
    auth, other = owner(client), owner(client)
    text = "The equal treatment rule follows 347 U.S. 483."
    identity = prepare(client, auth, text=text)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    await_status(client, auth, identity, "partial")
    results = client.get(route + "/results", headers=auth)
    assert results.status_code == 200, results.text
    claim = results.json()["claims"][0]
    original = claim["text"]
    assert claim["corrected_text"] is None
    assert claim["propositions_stale"] is False
    first = _correct(client, auth, identity, claim["id"], "Equal treatment is required.")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["original_text"] == original
    assert body["corrected_text"] == "Equal treatment is required."
    assert body["propositions_stale"] is True
    assert len(body["history"]) == 1
    assert "rerun" in body["limitation"]
    second = _correct(client, auth, identity, claim["id"], "Equal access remains required.")
    assert second.status_code == 200, second.text
    assert len(second.json()["history"]) == 2
    refreshed = client.get(route + "/results", headers=auth).json()["claims"][0]
    assert refreshed["text"] == original
    assert refreshed["corrected_text"] == "Equal access remains required."
    assert refreshed["propositions_stale"] is True
    assert len(refreshed["correction_history"]) == 2
    assert all(link["support_status"] == "not_run" for link in refreshed["links"])
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        stored = session.scalar(select(Claim).where(Claim.id == UUID(claim["id"])))
        assert stored.text == text
        assert stored.text != stored.correction_history[-1]["corrected_text"]
        findings_before = list(
            session.scalars(select(Finding).where(Finding.analysis_id == UUID(identity)))
        )
        links = list(
            session.scalars(
                select(ClaimAuthorityLink).where(ClaimAuthorityLink.claim_id == stored.id)
            )
        )
        analysis = session.get(Analysis, UUID(identity))
        assert all(link.support_status == "not_run" for link in links)
        assert "citations" in analysis.stage_states
        assert "claims" in analysis.stage_states
        assert len(findings_before) == len(
            list(session.scalars(select(Finding).where(Finding.analysis_id == UUID(identity))))
        )
        reason = (analysis.stage_states.get("propositions") or {}).get("reason", "")
        assert "stale" in str(reason).lower()
    foreign = _correct(client, other, identity, claim["id"], "Foreign session edit.")
    assert foreign.status_code == 404
    assert client.get(route + "/results", headers=other).status_code == 404
    missing = _correct(client, auth, identity, "00000000-0000-0000-0000-000000000000", "Nope.")
    assert missing.status_code == 404
    clone = client.post(route + "/rerun", headers=auth)
    assert clone.status_code == 201, clone.text
    clone_results = client.get(
        f"/api/v1/analyses/{clone.json()['analysis_id']}/results", headers=auth
    )
    assert clone_results.status_code == 200
    assert clone_results.json()["claims"] == []


def test_expired_analysis_corrections_are_not_found(private_client):
    client = private_client
    configure(client)
    auth = owner(client)
    text = "The rule follows 347 U.S. 483."
    identity = prepare(client, auth, text=text)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    await_status(client, auth, identity, "partial")
    claim_id = client.get(route + "/results", headers=auth).json()["claims"][0]["id"]
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory.begin() as session:
        session.get(Analysis, UUID(identity)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert _correct(client, auth, identity, claim_id, "Expired edit.").status_code == 404
