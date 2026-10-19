from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from filingguard.modules.claim_corrections.text import (
    latest_corrected_text,
    proposition_text,
    uses_user_correction,
)


def claim(*, text="Original extraction.", history=None):
    return SimpleNamespace(text=text, correction_history=history or [])


def test_original_text_is_used_until_a_correction_exists():
    row = claim()
    assert proposition_text(row) == "Original extraction."
    assert latest_corrected_text(row) is None
    assert uses_user_correction(row) is False


def test_latest_history_entry_is_distinct_from_original_text():
    row = claim(
        history=[
            {
                "id": str(uuid4()),
                "corrected_text": "First correction.",
                "created_at": datetime.now(UTC).isoformat(),
            },
            {
                "id": str(uuid4()),
                "corrected_text": "User-corrected extraction.",
                "created_at": datetime.now(UTC).isoformat(),
            },
        ]
    )
    assert row.text == "Original extraction."
    assert latest_corrected_text(row) == "User-corrected extraction."
    assert proposition_text(row) == "User-corrected extraction."
    assert uses_user_correction(row) is True


def test_blank_history_values_cannot_replace_original_extraction():
    row = claim(history=[{"id": str(uuid4()), "corrected_text": "   "}])
    assert proposition_text(row) == "Original extraction."
    assert uses_user_correction(row) is False
