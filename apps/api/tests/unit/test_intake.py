"""Unit tests for document intake validation, court profile allowlisting, and contracts."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from filingguard.api.contracts import CourtProfileSummary
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.documents.intake import PROFILES, prepare


def test_registered_profiles_metadata():
    profile_map = {p.id: p for p in PROFILES}
    assert "unverified" in profile_map
    assert "synthetic-demo-v1" in profile_map
    assert "us-txnd-lr7-2f-v1" in profile_map

    txnd = profile_map["us-txnd-lr7-2f-v1"]
    assert txnd.is_demo is False
    assert txnd.applicability == "verified"
    assert "Northern District of Texas" in txnd.name

    demo = profile_map["synthetic-demo-v1"]
    assert demo.is_demo is True
    assert demo.applicability == "synthetic"

    unverified = profile_map["unverified"]
    assert unverified.is_demo is False
    assert unverified.applicability == "unknown"


def test_court_profile_summary_contract_validation():
    # Demo profile must be synthetic
    with pytest.raises(ValidationError):
        CourtProfileSummary(
            id="demo", version="v1", name="Demo", is_demo=True, applicability="verified"
        )

    # Non-demo profile can be verified
    summary = CourtProfileSummary(
        id="real", version="v1", name="Real", is_demo=False, applicability="verified"
    )
    assert summary.applicability == "verified"


def test_prepare_profile_allowlist():
    lifecycle = MagicMock()
    doc = extract_text("Test paragraph content for filing.")
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    # In live mode:
    # 1. "unverified" is allowed
    # 2. "us-txnd-lr7-2f-v1" is allowed
    # 3. "synthetic-demo-v1" is rejected
    # 4. Unknown is rejected
    lifecycle.repository.list_analyses.return_value = []

    # Rejection of demo profile in live mode
    with pytest.raises(ValueError, match="Unknown or inapplicable court profile"):
        prepare(
            lifecycle,
            "owner_hash",
            expires_at,
            doc,
            name="Doc",
            court_profile_id="synthetic-demo-v1",
            ai_used=True,
            demo=False,
        )

    # Rejection of unknown profile in live mode
    with pytest.raises(ValueError, match="Unknown or inapplicable court profile"):
        prepare(
            lifecycle,
            "owner_hash",
            expires_at,
            doc,
            name="Doc",
            court_profile_id="unknown-court",
            ai_used=True,
            demo=False,
        )

    # In demo mode:
    # 1. "synthetic-demo-v1" is allowed
    # 2. "unverified" is allowed
    # 3. "us-txnd-lr7-2f-v1" is rejected
    with pytest.raises(ValueError, match="Unknown or inapplicable court profile"):
        prepare(
            lifecycle,
            "owner_hash",
            expires_at,
            doc,
            name="Doc",
            court_profile_id="us-txnd-lr7-2f-v1",
            ai_used=True,
            demo=True,
        )
