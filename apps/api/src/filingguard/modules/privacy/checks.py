"""Conservative local privacy findings; never a legal redaction verdict."""

import re
from dataclasses import dataclass
from datetime import datetime

from filingguard.modules.privacy.service import mask_excerpt


@dataclass(frozen=True)
class PrivacySignal:
    kind: str
    start: int
    end: int
    severity: str
    masked_snippet: str


_EXCLUDED_NAME_TERMS = frozenset(
    {
        "court", "judge", "justice", "state", "united", "states", "federal", "rule",
        "rules", "procedure", "plaintiff", "plaintiffs", "defendant", "defendants",
        "appellant", "appellee", "petitioner", "respondent", "counsel", "attorney",
        "county", "board", "district", "department", "hospital", "school", "schools",
        "service", "services", "police", "officer", "doctor", "dr", "mr", "mrs", "ms",
        "act", "section", "article", "clause", "amendment", "statute", "code",
        "america", "city", "bank", "company", "corporation", "inc", "llc", "ltd",
    }
)


def detect_sensitive(text: str) -> tuple[PrivacySignal, ...]:
    masked = mask_excerpt(text, 0, len(text))
    signals = []
    for item in masked.detections:
        if item.kind not in {"ssn", "financial_account", "birth_date", "minor_name"}:
            continue
        if item.kind == "birth_date":
            raw = text[item.start : item.end]
            if not _valid_full_date(raw):
                continue
        if item.kind == "minor_name":
            raw = text[item.start : item.end]
            if not _valid_minor_name(raw, text, item.start):
                continue
        left, right = max(0, item.start - 28), min(len(text), item.end + 28)
        signals.append(
            PrivacySignal(
                kind=item.kind,
                start=item.start,
                end=item.end,
                severity="high" if item.kind in {"ssn", "minor_name"} else "medium",
                masked_snippet=masked.text[left:right].replace("\n", " "),
            )
        )
    return tuple(signals)


def _valid_full_date(value: str) -> bool:
    parts = re.split(r"[/-]", value)
    try:
        if len(parts[0]) == 4:
            datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts[2]) == 4:
            datetime(int(parts[2]), int(parts[0]), int(parts[1]))
        else:
            return False
    except (ValueError, IndexError):
        return False
    return True


def _valid_minor_name(name: str, full_text: str, start: int) -> bool:
    words = name.strip().split()
    if not (2 <= len(words) <= 4):
        return False
    # Exclude initials which are compliant under Fed. R. Civ. P. 5.2(a)(3)
    if all(len(w.rstrip(".")) <= 1 for w in words):
        return False
    if any(not w[0].isupper() for w in words):
        return False
    if any(w.lower().rstrip(".,;") in _EXCLUDED_NAME_TERMS for w in words):
        return False
    # Exclude case citation contexts where 'Minor' or related terms are party names
    prefix = full_text[max(0, start - 30) : start]
    if re.search(r"\b(?:v\.|versus|in\s+re)\s*$", prefix, re.I):
        return False
    return True
