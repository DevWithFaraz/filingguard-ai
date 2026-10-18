"""Reference sources preserve limits instead of silently becoming court profiles."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from filingguard.modules.court_rules.service import evaluate_disclosure, load_profile
from filingguard.modules.court_rules.source_registry import (
    ReferenceCourtRuleSource,
    load_reference_source,
    load_reference_sources,
)
from filingguard.modules.documents.intake import prepare


def test_reference_sources_are_official_traceable_and_non_active():
    sources = load_reference_sources()

    assert [source.id for source in sources] == [
        "us-ohsd-jlg-ai-2025-10-21",
        "us-txs-general-order-2025-04",
    ]
    assert all(source.activation_status == "reference_only" for source in sources)
    assert all(source.runtime_profile_id is None for source in sources)
    assert all(source.current_effective_status == "unconfirmed" for source in sources)
    assert all(source.activation_blockers for source in sources)
    assert all(source.official_source_url.host.endswith("uscourts.gov") for source in sources)

    ohio = sources[0]
    texas = sources[1]
    assert ohio.judge_scope == "Hon. James L. Graham"
    assert ohio.applicability_status == "requires_case_scope_confirmation"
    assert texas.judge_scope is None
    assert texas.applicability_status == "not_a_disclosure_rule"

    for source in sources:
        with pytest.raises(ValueError, match="Unsupported court profile"):
            load_profile(source.id)
        evaluation = evaluate_disclosure(source.id, "AI USE DISCLOSURE", True, demo=False)
        assert evaluation.status == "unavailable"


def test_reference_source_rejects_accidental_activation_or_insecure_url():
    source = load_reference_source("us-ohsd-jlg-ai-2025-10-21").model_dump(mode="json")

    source["runtime_profile_id"] = "us-ohsd-jlg-ai-2025-10-21"
    with pytest.raises(ValidationError):
        ReferenceCourtRuleSource.model_validate(source)

    source["runtime_profile_id"] = None
    source["official_source_url"] = "http://www.ohsd.uscourts.gov/order.pdf"
    with pytest.raises(ValidationError, match="HTTPS"):
        ReferenceCourtRuleSource.model_validate(source)


def test_reference_source_cannot_be_selected_for_live_intake():
    source = load_reference_source("us-ohsd-jlg-ai-2025-10-21")

    with pytest.raises(ValueError, match="Unknown or inapplicable court profile"):
        prepare(
            None,
            "owner",
            datetime.now(UTC),
            None,
            name="Unconfigured filing",
            court_profile_id=source.id,
            ai_used=True,
        )
