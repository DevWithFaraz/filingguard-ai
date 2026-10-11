"""Local conservative masking; never a guarantee that all sensitive data is found."""

import re
from dataclasses import dataclass

PATTERNS = {
    "ssn": r"\b\d{3}[- ]\d{2}[- ]\d{4}\b",
    "email": r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w-]|\.(?=[\w-]))",
    "phone": r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)",
    "financial_account": (
        r"(?i)\b(?:account|routing|card)(?:\s+(?:number|no\.?))?"
        r"\s*[:#]?\s*(\d[\d -]{6,24}\d)\b"
    ),
    "birth_date": r"(?i)\b(?:DOB|date of birth)\s*[:=]?\s*(\d{1,4}[/-]\d{1,2}[/-]\d{1,4})\b",
}


@dataclass(frozen=True)
class Detection:
    kind: str
    start: int
    end: int


@dataclass(frozen=True)
class MaskedExcerpt:
    text: str
    original_start: int
    original_end: int
    detections: tuple[Detection, ...]
    method: str = "local-pattern-mask-v1"
    limitation: str = "Heuristic masking can miss names and contextual identifiers."


def mask_excerpt(document: str, start: int, end: int) -> MaskedExcerpt:
    if not 0 <= start < end <= len(document) or end - start > 100000:
        raise ValueError("Invalid provider excerpt boundary")
    detections = []
    masked = list(document[start:end])
    # Detect on the whole snapshot so clipping an identifier cannot evade masking.
    for kind, pattern in PATTERNS.items():
        for match in re.finditer(pattern, document):
            left, right = match.span(1 if match.lastindex else 0)
            if left < end and right > start:
                detections.append(Detection(kind, left, right))
                for index in range(max(left, start), min(right, end)):
                    masked[index - start] = "*"
    return MaskedExcerpt("".join(masked), start, end, tuple(detections))
