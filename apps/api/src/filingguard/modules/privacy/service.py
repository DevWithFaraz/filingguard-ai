"""Local conservative masking; never a guarantee that all sensitive data is found."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

from filingguard.modules.court_rules.service import PrivacyPolicyBinding

PATTERNS = {
    "ssn": r"\b\d{3}[- ]\d{2}[- ]\d{4}\b",
    "email": r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w-]|\.(?=[\w-]))",
    "phone": r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)",
    "financial_account": (
        r"(?i)\b(?:account|routing|card)(?:\s+(?:number|no\.?))?"
        r"\s*[:#]?\s*(\d[\d -]{6,24}\d)\b"
    ),
    "birth_date": r"(?i)\b(?:DOB|date of birth)\s*[:=]?\s*(\d{1,4}[/-]\d{1,2}[/-]\d{1,4})\b",
    "minor_name": (
        r"\b(?i:minor\s+child(?:ren)?|minor\s+son|minor\s+daughter|minor\s+ward"
        r"|the\s+minor\s+child|a\s+minor\s+child|minor(?:\s+name)?\s*[:=])(?:\s*,)?\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b"
        r"|\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+),\s*(?i:a\s+minor(?:\s+child)?|\(a\s+minor\))\b"
        r"|\b(?i:on\s+behalf\s+of|next\s+friend\s+of|guardian\s+ad\s+litem\s+for|as\s+guardian\s+of)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)(?:,\s*(?i:a\s+minor)|\s+\((?i:a\s+minor)\))\b"
    ),
}


@dataclass(frozen=True)
class KnownPrivacyPolicy:
    policy_id: str
    version: str
    extra_identifier_kinds: tuple[str, ...]
    effective_from: date
    effective_to: date
    official_source_url: str | None
    reminder: str
    synthetic: bool = False


@dataclass(frozen=True)
class PrivacyPolicyResolution:
    status: Literal["not_configured", "applied", "unavailable"]
    extra_identifier_kinds: tuple[str, ...] = ()
    reason: str | None = None
    reminder: str | None = None
    policy_id: str | None = None
    version: str | None = None


_KNOWN_PRIVACY_POLICIES: dict[str, KnownPrivacyPolicy] = {
    "synthetic-demo-privacy-v1": KnownPrivacyPolicy(
        policy_id="synthetic-demo-privacy-v1",
        version="synthetic-privacy-v1",
        extra_identifier_kinds=("email",),
        effective_from=date(2026, 1, 1),
        effective_to=date(2099, 12, 31),
        official_source_url=None,
        reminder=(
            "Training-only extra identifier scan (email). Not a jurisdiction redaction rule."
        ),
        synthetic=True,
    ),
    "us-frcp-5-2-v1": KnownPrivacyPolicy(
        policy_id="us-frcp-5-2-v1",
        version="frcp-5-2-checked-2026-10-19",
        extra_identifier_kinds=(),
        effective_from=date(2007, 12, 1),
        effective_to=date(2099, 12, 31),
        official_source_url=(
            "https://www.uscourts.gov/rules-policies/current-rules-practice-procedure/"
            "federal-rules-civil-procedure"
        ),
        reminder=(
            "Fed. R. Civ. P. 5.2 reminder: review redaction of listed identifiers. "
            "Automated detection is not a compliance determination."
        ),
    ),
}

_SUPPORTED_EXTRA_KINDS = frozenset({"email", "phone"})


def resolve_privacy_policy(
    binding: PrivacyPolicyBinding | None,
    *,
    is_demo: bool,
    as_of: date | None = None,
) -> PrivacyPolicyResolution:
    """Apply a versioned jurisdiction policy only when the catalog entry is current."""

    if binding is None:
        return PrivacyPolicyResolution(status="not_configured")
    spec = _KNOWN_PRIVACY_POLICIES.get(binding.policy_id)
    today = as_of or date.today()
    unavailable = (
        "Jurisdictional privacy policy is unknown, stale, or source-mismatched; "
        "extra identifier rules were not applied and this is not a pass."
    )
    if spec is None or spec.version != binding.version:
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    if spec.synthetic != is_demo:
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    if not (spec.effective_from <= today <= spec.effective_to):
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    if spec.official_source_url and binding.source_url != spec.official_source_url:
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    requested = tuple(binding.extra_identifier_kinds)
    if any(kind not in _SUPPORTED_EXTRA_KINDS for kind in requested):
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    if any(kind not in spec.extra_identifier_kinds for kind in requested):
        return PrivacyPolicyResolution(
            status="unavailable",
            reason=unavailable,
            policy_id=binding.policy_id,
            version=binding.version,
        )
    kinds = requested if requested else spec.extra_identifier_kinds
    return PrivacyPolicyResolution(
        status="applied",
        extra_identifier_kinds=kinds,
        reminder=binding.reminder or spec.reminder,
        policy_id=spec.policy_id,
        version=spec.version,
    )


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
            target_group = match.lastindex if match.lastindex else 0
            left, right = match.span(target_group)
            if left < end and right > start:
                detections.append(Detection(kind, left, right))
                for index in range(max(left, start), min(right, end)):
                    masked[index - start] = "*"
    return MaskedExcerpt("".join(masked), start, end, tuple(detections))
