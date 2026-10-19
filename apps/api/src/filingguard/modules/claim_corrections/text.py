"""Original extraction vs user-corrected proposition text."""

from typing import Any

MAX_CORRECTION_CHARS = 8000
MAX_HISTORY = 20


def history_entries(claim: Any) -> list[dict]:
    raw = getattr(claim, "correction_history", None) or []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def latest_corrected_text(claim: Any) -> str | None:
    entries = history_entries(claim)
    if not entries:
        return None
    value = entries[-1].get("corrected_text")
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def proposition_text(claim: Any) -> str:
    """Text proposition review should use; original extraction remains claim.text."""
    return latest_corrected_text(claim) or claim.text


def uses_user_correction(claim: Any) -> bool:
    return latest_corrected_text(claim) is not None
