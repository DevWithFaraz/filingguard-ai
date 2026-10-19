"""Statute source adapters; transport failures never become not-found."""

from typing import Protocol

import httpx

from filingguard.core.config import Settings
from filingguard.integrations.providers.runtime import ProviderBudget, ProviderUnavailable
from filingguard.modules.statutes.schemas import (
    LIMITATION,
    LawIdentity,
    StatuteLookupResult,
    StatuteStatus,
)


class StatuteAdapter(Protocol):
    def lookup(self, identity: LawIdentity) -> StatuteLookupResult: ...


def _unavailable(identity: LawIdentity, reason: str) -> StatuteLookupResult:
    return StatuteLookupResult(
        status=StatuteStatus.UNAVAILABLE,
        query_text=identity.raw_text,
        reason=reason,
        jurisdiction=identity.jurisdiction,
        coverage_limitation=LIMITATION,
        method="statute-http-v1",
    )


class CatalogStatuteAdapter:
    """In-memory public/synthetic catalog; used by tests and explicit local config."""

    def __init__(self, records: dict[str, dict]):
        self._records = dict(records)

    def lookup(self, identity: LawIdentity) -> StatuteLookupResult:
        record = self._records.get(identity.normalized_key)
        if record is None:
            return StatuteLookupResult(
                status=StatuteStatus.NOT_FOUND,
                query_text=identity.raw_text,
                reason="not_found_in_statute_source",
                jurisdiction=identity.jurisdiction,
                coverage_limitation=(
                    "The configured statute catalog does not contain this citation. "
                    "Absence from this catalog does not prove fabrication. " + LIMITATION
                ),
                method="statute-catalog-v1",
            )
        return StatuteLookupResult(
            status=StatuteStatus.VERIFIED,
            query_text=identity.raw_text,
            reason="matched_statute_catalog",
            jurisdiction=str(record.get("jurisdiction") or identity.jurisdiction),
            version=record.get("version"),
            effective_date=record.get("effective_date"),
            coverage_limitation=str(record.get("coverage_limitation") or LIMITATION),
            source_url=record.get("source_url"),
            method="statute-catalog-v1",
        )


class HttpStatuteAdapter:
    """HTTP lookup with injected transport. 429/5xx/timeout map to unavailable."""

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.BaseTransport | None = None,
        budget: ProviderBudget | None = None,
        timeout: float = 5.0,
    ) -> None:
        if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
            raise ProviderUnavailable("invalid_request")
        self._base = base_url.rstrip("/")
        self._transport = transport
        self._budget = budget
        self._timeout = timeout

    def lookup(self, identity: LawIdentity) -> StatuteLookupResult:
        timeout = self._timeout
        if self._budget is not None:
            try:
                timeout = min(timeout, self._budget.remaining())
            except ProviderUnavailable:
                return _unavailable(identity, "timeout")
        if timeout <= 0:
            return _unavailable(identity, "timeout")
        try:
            with httpx.Client(
                transport=self._transport,
                follow_redirects=False,
                trust_env=False,
                timeout=timeout,
            ) as client:
                response = client.get(
                    f"{self._base}/lookup",
                    params={"citation": identity.normalized_key},
                )
        except httpx.TimeoutException:
            return _unavailable(identity, "timeout")
        except httpx.HTTPError:
            return _unavailable(identity, "network_failure")
        if response.status_code == 429:
            return _unavailable(identity, "rate_limited")
        if response.status_code >= 500:
            return _unavailable(identity, "http_failure")
        if response.status_code != 200:
            return _unavailable(identity, "http_failure")
        try:
            payload = response.json()
        except ValueError:
            return _unavailable(identity, "invalid_response")
        if not isinstance(payload, dict):
            return _unavailable(identity, "invalid_response")
        if payload.get("found") is False:
            return StatuteLookupResult(
                status=StatuteStatus.NOT_FOUND,
                query_text=identity.raw_text,
                reason="not_found_in_statute_source",
                jurisdiction=identity.jurisdiction,
                coverage_limitation=(
                    "The configured statute source did not return this citation. "
                    "Absence does not prove fabrication. " + LIMITATION
                ),
                method="statute-http-v1",
            )
        if payload.get("found") is not True:
            return _unavailable(identity, "invalid_response")
        return StatuteLookupResult(
            status=StatuteStatus.VERIFIED,
            query_text=identity.raw_text,
            reason="matched_statute_source",
            jurisdiction=str(payload.get("jurisdiction") or identity.jurisdiction),
            version=payload.get("version") if isinstance(payload.get("version"), str) else None,
            effective_date=(
                payload.get("effective_date")
                if isinstance(payload.get("effective_date"), str)
                else None
            ),
            coverage_limitation=str(payload.get("coverage_limitation") or LIMITATION),
            source_url=payload.get("source_url")
            if isinstance(payload.get("source_url"), str)
            else None,
            method="statute-http-v1",
        )


def configured_statute_adapter(
    *,
    budget: ProviderBudget | None = None,
    transport: httpx.BaseTransport | None = None,
    settings: Settings | None = None,
) -> StatuteAdapter | None:
    resolved = settings or Settings()
    url = (resolved.statute_source_url or "").strip()
    if not url.startswith(("http://", "https://")):
        return None
    return HttpStatuteAdapter(url, transport=transport, budget=budget)
