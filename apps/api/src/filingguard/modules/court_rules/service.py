"""Validated, explicitly scoped court profiles and deterministic disclosure checks."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DisclosureRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str = Field(min_length=1)
    trigger: Literal["ai_used"]
    requirement: str = Field(min_length=1)
    heading: str = Field(min_length=1)
    placement: Literal["anywhere", "first_page"] = "anywhere"


class PageLimitRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str = Field(min_length=1)
    max_pages: int = Field(ge=1, le=500)
    filing_scope: str = Field(min_length=1)
    requirement: str = Field(min_length=1)


class RequiredHeadingRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str = Field(min_length=1)
    heading: str = Field(min_length=1)
    requirement: str = Field(min_length=1)
    placement: Literal["anywhere", "first_page"] = "anywhere"


class PrivacyPolicyBinding(BaseModel):
    """Versioned jurisdiction privacy policy reference stored on a court profile."""

    model_config = ConfigDict(extra="forbid")
    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    source_checked_on: date
    extra_identifier_kinds: tuple[str, ...] = ()
    reminder: str | None = None

    @field_validator("source_url")
    @classmethod
    def https_if_url(cls, value: str) -> str:
        stripped = value.strip()
        if "://" in stripped and not stripped.startswith("https://"):
            raise ValueError("Privacy policy source URLs must use HTTPS")
        return stripped


class CourtProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    court_scope: str = Field(min_length=1)
    judge_scope: str | None
    is_demo: bool
    ai_disclosure: DisclosureRule
    page_limit: PageLimitRule | None = None
    required_headings: tuple[RequiredHeadingRule, ...] = ()
    privacy_policy: PrivacyPolicyBinding | None = None

    @model_validator(mode="after")
    def valid_period(self):
        if self.effective_to < self.effective_from:
            raise ValueError("Profile effective dates are reversed")
        return self


class DisclosureEvaluation(BaseModel):
    status: Literal["present", "missing", "not_triggered", "unavailable"]
    requirement: str | None = None
    reason: str | None = None
    rule_id: str | None = None


class FormatEvaluation(BaseModel):
    status: Literal["present", "missing", "exceeded", "within_limit", "unavailable"]
    check: Literal["page_limit", "heading"]
    requirement: str | None = None
    reason: str | None = None
    rule_id: str | None = None


_SUPPORTED_PROFILES = frozenset({"synthetic-demo-v1", "us-txnd-lr7-2f-v1"})


def load_profile(profile_id: str) -> CourtProfile:
    if profile_id not in _SUPPORTED_PROFILES:
        raise ValueError("Unsupported court profile")
    path = Path(__file__).parent / "profiles" / f"{profile_id}.json"
    profile = CourtProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if profile.id != profile_id:
        raise ValueError("Court profile identity mismatch")
    return profile


def _has_heading(content: str, heading: str) -> bool:
    target = heading.strip().casefold()
    return any(line.strip().casefold() == target for line in content.splitlines())


def _evaluate_heading_placement(
    *,
    text: str,
    heading: str,
    placement: Literal["anywhere", "first_page"],
    pages: tuple[str, ...] | list[str] | None,
    requirement: str,
    rule_id: str,
    first_page_later_reason: str,
) -> DisclosureEvaluation:
    if placement == "first_page":
        if pages is not None and len(pages) > 0:
            if _has_heading(pages[0], heading):
                return DisclosureEvaluation(
                    status="present",
                    requirement=requirement,
                    rule_id=rule_id,
                    reason=(
                        "Heading presence only; substantive disclosure content and legal "
                        "compliance require independent human review."
                    ),
                )
            if any(_has_heading(p, heading) for p in pages[1:]):
                return DisclosureEvaluation(
                    status="missing",
                    requirement=requirement,
                    rule_id=rule_id,
                    reason=first_page_later_reason,
                )
            return DisclosureEvaluation(
                status="missing",
                requirement=requirement,
                rule_id=rule_id,
                reason=(
                    f"Required disclosure heading '{heading}' was not found on the first page."
                ),
            )
        if _has_heading(text, heading):
            return DisclosureEvaluation(
                status="present",
                requirement=requirement,
                rule_id=rule_id,
                reason=(
                    "Heading found in plain text; unpaginated submission lacks page boundaries "
                    "so first-page placement cannot be strictly verified."
                ),
            )
        return DisclosureEvaluation(
            status="missing",
            requirement=requirement,
            rule_id=rule_id,
            reason=f"Required disclosure heading '{heading}' was not found.",
        )

    present = _has_heading(text, heading)
    return DisclosureEvaluation(
        status="present" if present else "missing",
        requirement=requirement,
        rule_id=rule_id,
        reason=(
            "Heading presence only; substantive disclosure content and legal compliance "
            "require independent human review."
        )
        if present
        else "Required disclosure heading was not found",
    )


def evaluate_disclosure(
    profile_id: str,
    text: str,
    ai_used: bool,
    *,
    demo: bool,
    pages: tuple[str, ...] | list[str] | None = None,
    as_of: date | None = None,
) -> DisclosureEvaluation:
    if profile_id == "unverified":
        return DisclosureEvaluation(status="unavailable", reason="Court rules not configured")
    try:
        profile = load_profile(profile_id)
    except (ValueError, OSError, json.JSONDecodeError):
        return DisclosureEvaluation(status="unavailable", reason="Court profile unavailable")
    if profile.is_demo != demo:
        return DisclosureEvaluation(
            status="unavailable", reason="Court profile scope does not match review mode"
        )
    today = as_of or date.today()
    if not (profile.effective_from <= today <= profile.effective_to):
        return DisclosureEvaluation(
            status="unavailable", reason="Court profile outside effective period"
        )
    rule = profile.ai_disclosure
    if not ai_used:
        return DisclosureEvaluation(
            status="not_triggered", requirement=rule.requirement, rule_id=rule.rule_id
        )
    later_reason = (
        "Disclosure heading found on later page, but Local Rule 7.2(f) requires "
        "placement on the first page."
        if rule.placement == "first_page" and not profile.is_demo
        else "Required heading was found after the first page."
    )
    return _evaluate_heading_placement(
        text=text,
        heading=rule.heading,
        placement=rule.placement,
        pages=pages,
        requirement=rule.requirement,
        rule_id=rule.rule_id,
        first_page_later_reason=later_reason,
    )


def evaluate_page_limit(
    profile: CourtProfile,
    pages: tuple[str, ...] | list[str] | None,
) -> FormatEvaluation | None:
    rule = profile.page_limit
    if rule is None:
        return None
    if pages is None or len(pages) == 0:
        return FormatEvaluation(
            status="unavailable",
            check="page_limit",
            requirement=rule.requirement,
            rule_id=rule.rule_id,
            reason=(
                "Page-limit rule not evaluated without page boundaries; "
                "unknown length is not a pass."
            ),
        )
    count = len(pages)
    if count > rule.max_pages:
        return FormatEvaluation(
            status="exceeded",
            check="page_limit",
            requirement=rule.requirement,
            rule_id=rule.rule_id,
            reason=(
                f"Extracted page count {count} exceeds the versioned limit of "
                f"{rule.max_pages} for {rule.filing_scope}."
            ),
        )
    return FormatEvaluation(
        status="within_limit",
        check="page_limit",
        requirement=rule.requirement,
        rule_id=rule.rule_id,
        reason=(
            f"Extracted page count {count} is within the versioned limit of "
            f"{rule.max_pages}; this is not a court-counted-page determination."
        ),
    )


def evaluate_required_headings(
    profile: CourtProfile,
    text: str,
    pages: tuple[str, ...] | list[str] | None,
) -> tuple[FormatEvaluation, ...]:
    results: list[FormatEvaluation] = []
    for rule in profile.required_headings:
        later_reason = (
            f"Heading '{rule.heading}' was found after the first page, but this "
            "versioned rule requires first-page placement."
        )
        mapped = _evaluate_heading_placement(
            text=text,
            heading=rule.heading,
            placement=rule.placement,
            pages=pages,
            requirement=rule.requirement,
            rule_id=rule.rule_id,
            first_page_later_reason=later_reason,
        )
        reason = mapped.reason
        if mapped.status == "missing" and reason == "Required disclosure heading was not found":
            reason = f"Required heading '{rule.heading}' was not found"
        elif mapped.status == "missing" and reason and "disclosure heading" in reason:
            reason = reason.replace("disclosure heading", "heading")
        results.append(
            FormatEvaluation(
                status="present" if mapped.status == "present" else "missing",
                check="heading",
                requirement=mapped.requirement,
                rule_id=mapped.rule_id,
                reason=reason,
            )
        )
    return tuple(results)


def evaluate_format_rules(
    profile: CourtProfile,
    text: str,
    pages: tuple[str, ...] | list[str] | None,
) -> tuple[FormatEvaluation, ...]:
    results: list[FormatEvaluation] = []
    page_limit = evaluate_page_limit(profile, pages)
    if page_limit is not None:
        results.append(page_limit)
    results.extend(evaluate_required_headings(profile, text, pages))
    return tuple(results)
