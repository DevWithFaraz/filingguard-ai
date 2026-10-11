"""Validated, explicitly scoped court profiles and deterministic disclosure checks."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DisclosureRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str = Field(min_length=1)
    trigger: Literal["ai_used"]
    requirement: str = Field(min_length=1)
    heading: str = Field(min_length=1)


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


def load_profile(profile_id: str) -> CourtProfile:
    path = Path(__file__).parent / "profiles" / f"{profile_id}.json"
    if profile_id != "synthetic-demo-v1":
        raise ValueError("Unsupported court profile")
    profile = CourtProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if profile.id != profile_id:
        raise ValueError("Court profile identity mismatch")
    return profile


def evaluate_disclosure(
    profile_id: str, text: str, ai_used: bool, *, demo: bool, as_of: date | None = None
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
    if not profile.effective_from <= today <= profile.effective_to:
        return DisclosureEvaluation(
            status="unavailable", reason="Court profile outside effective period"
        )
    rule = profile.ai_disclosure
    if not ai_used:
        return DisclosureEvaluation(
            status="not_triggered", requirement=rule.requirement, rule_id=rule.rule_id
        )
    # Require a standalone heading; a passing mention in an argument is not disclosure.
    present = any(line.strip().casefold() == rule.heading.casefold() for line in text.splitlines())
    return DisclosureEvaluation(
        status="present" if present else "missing",
        requirement=rule.requirement,
        rule_id=rule.rule_id,
        reason="Heading presence only; content and legal sufficiency require human review"
        if present
        else "Required disclosure heading was not found",
    )
