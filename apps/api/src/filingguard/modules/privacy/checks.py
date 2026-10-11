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


def detect_sensitive(text: str) -> tuple[PrivacySignal, ...]:
    masked = mask_excerpt(text, 0, len(text))
    signals = []
    for item in masked.detections:
        if item.kind not in {"ssn", "financial_account", "birth_date"}:
            continue
        if item.kind == "birth_date":
            raw = text[item.start : item.end]
            if not _valid_full_date(raw):
                continue
        left, right = max(0, item.start - 28), min(len(text), item.end + 28)
        signals.append(
            PrivacySignal(
                kind=item.kind,
                start=item.start,
                end=item.end,
                severity="high" if item.kind == "ssn" else "medium",
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
