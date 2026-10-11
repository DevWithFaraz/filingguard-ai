"""CourtListener adapter for citation verification with bounded error mapping.

Never converts timeout, 429, 5xx, or network failure into not_found.
Credentials and raw payloads are never logged or exposed in result records.
"""

import hashlib
import re
import time
from datetime import UTC, datetime
from html.parser import HTMLParser

import httpx

from filingguard.core.config import Settings
from filingguard.integrations.courtlistener.schemas import (
    AMBIGUOUS_LIMITATION,
    INVALID_LIMITATION,
    NOT_FOUND_LIMITATION,
    UNAVAILABLE_LIMITATION,
    CourtListenerCluster,
    CourtListenerLookupResult,
    CourtListenerOpinion,
    CourtListenerResolvedAuthority,
)
from filingguard.integrations.providers.runtime import (
    ProviderBudget,
    ProviderDeadline,
    ProviderUnavailable,
)
from filingguard.integrations.providers.transport import (
    BoundedProviderClient,
    ProviderPolicy,
)
from filingguard.modules.analyses.schemas import CitationStatus

MAX_CITATION_LENGTH = 500


def _parse_year(date_filed: str | None) -> int | None:
    if not date_filed:
        return None
    match = re.match(r"^(\d{4})", str(date_filed).strip())
    if match:
        try:
            year = int(match.group(1))
            if 1700 <= year <= 2100:
                return year
        except ValueError:
            pass
    return None


def _parse_court_code(court: str | None) -> str | None:
    if not court:
        return None
    court_str = str(court).strip()
    if "/courts/" in court_str:
        parts = court_str.rstrip("/").split("/")
        return parts[-1]
    return court_str


def _parse_opinion_ids(sub_opinions: list[object] | None) -> list[int]:
    if not sub_opinions:
        return []
    ids: list[int] = []
    for item in sub_opinions:
        if isinstance(item, int):
            ids.append(item)
        elif isinstance(item, str):
            match = re.search(r"/opinions/(\d+)/?", item)
            if match:
                ids.append(int(match.group(1)))
            elif item.isdigit():
                ids.append(int(item))
    return ids


def _parse_cluster(cluster_data: dict, norm_cit: str | None) -> CourtListenerCluster:
    cid = int(cluster_data.get("id", 0))
    case_name = cluster_data.get("case_name")
    cit = norm_cit or cluster_data.get("citation")
    court = _parse_court_code(cluster_data.get("court"))
    date_filed = cluster_data.get("date_filed")
    year = _parse_year(date_filed)
    sub_opinions = cluster_data.get("sub_opinions") or []
    opinion_ids = _parse_opinion_ids(sub_opinions)
    abs_url = cluster_data.get("absolute_url")
    source_url = (
        f"https://www.courtlistener.com{abs_url}"
        if abs_url and abs_url.startswith("/")
        else abs_url
    )
    return CourtListenerCluster(
        id=cid,
        case_name=case_name,
        citation=cit,
        court=court,
        year=year,
        date_filed=date_filed,
        sub_opinions=sub_opinions,
        opinion_ids=opinion_ids,
        absolute_url=abs_url,
        source_url=source_url,
    )


LEAD_OPINION_TYPES = {"010combined", "015unamani", "020lead", "025plurality", "majority"}
DISSENT_OPINION_TYPES = {
    "030concurrence",
    "035concurrence_in_part",
    "040dissent",
    "dissent",
    "concurrence",
}
OPINION_TEXT_FIELDS = (
    "plain_text",
    "html_with_citations",
    "html",
    "html_lawbox",
    "html_columbia",
    "xml_harvard",
)


class OpinionTextParser(HTMLParser):
    """HTML to plain text conversion preserving paragraph and block boundaries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden += 1
        elif tag in {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        elif tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def clean_opinion_html(html_content: str) -> str:
    """Extract readable text from opinion HTML, stripping scripts and styling."""
    if not html_content or not isinstance(html_content, str):
        return ""
    parser = OpinionTextParser()
    parser.feed(html_content)
    return "".join(parser.parts)


def _parse_opinion(opinion_data: dict, opinion_id: int) -> CourtListenerOpinion:
    op_type = opinion_data.get("type")
    author = opinion_data.get("author") or opinion_data.get("author_str")
    per_curiam = bool(opinion_data.get("per_curiam", False))
    cluster_id = opinion_data.get("cluster_id")
    if cluster_id is None and isinstance(opinion_data.get("cluster"), str):
        match = re.search(r"/clusters/(\d+)/?", opinion_data["cluster"])
        if match:
            cluster_id = int(match.group(1))
    download_url = opinion_data.get("download_url")
    abs_url = opinion_data.get("absolute_url")
    source_url = (
        f"https://www.courtlistener.com{abs_url}"
        if abs_url and abs_url.startswith("/")
        else f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    )

    selected_field: str | None = None
    raw_content: str | None = None
    for field in OPINION_TEXT_FIELDS:
        val = opinion_data.get(field)
        if isinstance(val, str) and val.strip():
            selected_field = field
            raw_content = val
            break

    if selected_field is not None and raw_content is not None:
        if selected_field == "plain_text":
            text = raw_content
            text_conversion = "identity-v1"
        else:
            text = clean_opinion_html(raw_content)
            text_conversion = "htmlparser-block-boundaries-v1"

        if text and text.strip():
            text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            raw_sha256 = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
            return CourtListenerOpinion(
                id=opinion_id,
                cluster_id=cluster_id,
                opinion_type=op_type,
                author=author,
                per_curiam=per_curiam,
                text=text,
                text_field=selected_field,
                text_conversion=text_conversion,
                text_sha256=text_sha256,
                raw_sha256=raw_sha256,
                opinion_text_available=True,
                download_url=download_url,
                source_url=source_url,
                missing_text=False,
            )

    return CourtListenerOpinion(
        id=opinion_id,
        cluster_id=cluster_id,
        opinion_type=op_type,
        author=author,
        per_curiam=per_curiam,
        text=None,
        text_field=None,
        text_conversion=None,
        text_sha256=None,
        raw_sha256=None,
        opinion_text_available=False,
        download_url=download_url,
        source_url=source_url,
        missing_text=True,
    )



class CourtListenerCache:
    """Cache for public CourtListener responses within an analysis or session.

    Caches citation lookups, retrieved opinions, and resolved authorities.
    Deduplicates outbound HTTP requests for identical or normalized citation
    lookups during an analysis run.
    """

    def __init__(self) -> None:
        self._lookups: dict[str, CourtListenerLookupResult] = {}
        self._opinions: dict[int, CourtListenerOpinion] = {}
        self._authorities: dict[int, CourtListenerResolvedAuthority] = {}
        self.lookup_hits: int = 0
        self.lookup_misses: int = 0
        self.opinion_hits: int = 0
        self.opinion_misses: int = 0
        self.authority_hits: int = 0
        self.authority_misses: int = 0

    @staticmethod
    def normalize_key(citation_text: str) -> str:
        """Normalize whitespace in citation text for stable cache keys."""
        return " ".join(citation_text.strip().split())

    def get_lookup(self, citation_text: str) -> CourtListenerLookupResult | None:
        key = self.normalize_key(citation_text)
        result = self._lookups.get(key)
        if result is not None:
            self.lookup_hits += 1
            return result
        self.lookup_misses += 1
        return None

    def set_lookup(self, citation_text: str, result: CourtListenerLookupResult) -> None:
        key = self.normalize_key(citation_text)
        self._lookups[key] = result
        if result.normalized_citation:
            norm_key = self.normalize_key(result.normalized_citation)
            self._lookups[norm_key] = result

    def get_opinion(self, opinion_id: int) -> CourtListenerOpinion | None:
        opinion = self._opinions.get(opinion_id)
        if opinion is not None:
            self.opinion_hits += 1
            return opinion
        self.opinion_misses += 1
        return None

    def set_opinion(self, opinion_id: int, opinion: CourtListenerOpinion) -> None:
        self._opinions[opinion_id] = opinion

    def get_authority(self, cluster_id: int) -> CourtListenerResolvedAuthority | None:
        auth = self._authorities.get(cluster_id)
        if auth is not None:
            self.authority_hits += 1
            return auth
        self.authority_misses += 1
        return None

    def set_authority(self, cluster_id: int, authority: CourtListenerResolvedAuthority) -> None:
        self._authorities[cluster_id] = authority

    def clear(self) -> None:
        self._lookups.clear()
        self._opinions.clear()
        self._authorities.clear()
        self.lookup_hits = 0
        self.lookup_misses = 0
        self.opinion_hits = 0
        self.opinion_misses = 0
        self.authority_hits = 0
        self.authority_misses = 0

    @property
    def lookups(self) -> dict[str, CourtListenerLookupResult]:
        return dict(self._lookups)

    @property
    def opinions(self) -> dict[int, CourtListenerOpinion]:
        return dict(self._opinions)

    @property
    def authorities(self) -> dict[int, CourtListenerResolvedAuthority]:
        return dict(self._authorities)


class CourtListenerAdapter:
    """Bounded CourtListener citation verification adapter."""

    _default_transport: httpx.BaseTransport | None = None

    @classmethod
    def set_default_transport(cls, transport: httpx.BaseTransport | None) -> None:
        cls._default_transport = transport

    def __init__(
        self,
        token: str | None = None,
        *,
        budget: ProviderBudget | None = None,
        policy: ProviderPolicy | None = None,
        transport: httpx.BaseTransport | None = None,
        cache: CourtListenerCache | None = None,
    ) -> None:
        resolved_token = token
        if resolved_token is None:
            resolved_token = Settings().courtlistener_api_token

        if resolved_token is not None:
            resolved_token = resolved_token.strip()
            if (
                not resolved_token
                or len(resolved_token) > 4096
                or any(ord(char) < 33 or ord(char) > 126 for char in resolved_token)
            ):
                resolved_token = None

        self._token: str | None = resolved_token
        self._policy: ProviderPolicy = policy or ProviderPolicy()

        if budget is None:
            deadline = time.monotonic() + self._policy.call_timeout
            self._budget = ProviderBudget(deadline)
        else:
            self._budget = budget

        self._transport: httpx.BaseTransport | None = (
            transport if transport is not None else self._default_transport
        )
        self._client: BoundedProviderClient | None = None
        self._cache: CourtListenerCache = cache if cache is not None else CourtListenerCache()

    @property
    def cache(self) -> CourtListenerCache:
        return self._cache

    def __repr__(self) -> str:
        remaining = 0.0
        try:
            remaining = self._budget.remaining()
        except Exception:
            pass
        return (
            f"<CourtListenerAdapter authenticated={bool(self._token)} "
            f"remaining_seconds={remaining:.1f}>"
        )

    def __enter__(self) -> "CourtListenerAdapter":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _get_client(self) -> BoundedProviderClient:
        if not self._token:
            raise ProviderUnavailable("missing_token")
        if self._client is None or self._client._client.is_closed:
            self._client = BoundedProviderClient(
                provider="courtlistener",
                credential=self._token,
                budget=self._budget,
                policy=self._policy,
                transport=self._transport,
            )
        return self._client

    def _cache_and_return_lookup(
        self, query: str, result: CourtListenerLookupResult
    ) -> CourtListenerLookupResult:
        if result.status != CitationStatus.UNAVAILABLE:
            self._cache.set_lookup(query, result)
        return result

    def lookup_citation(self, citation_text: str) -> CourtListenerLookupResult:
        """Query CourtListener citation lookup for a single citation string."""
        if not isinstance(citation_text, str) or not citation_text.strip():
            return CourtListenerLookupResult(
                status=CitationStatus.INVALID,
                query_text=citation_text if isinstance(citation_text, str) else "",
                reason="empty_citation",
                limitation=INVALID_LIMITATION,
            )

        query = citation_text.strip()
        if len(query) > MAX_CITATION_LENGTH:
            return CourtListenerLookupResult(
                status=CitationStatus.INVALID,
                query_text=query,
                reason="citation_too_long",
                limitation=INVALID_LIMITATION,
            )

        cached = self._cache.get_lookup(query)
        if cached is not None:
            return cached

        if not self._token:
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason="missing_token",
                limitation=UNAVAILABLE_LIMITATION,
            )

        try:
            client = self._get_client()
            raw_response = client.request_json(
                "POST",
                "/api/rest/v4/citation-lookup/",
                payload={"text": query},
            )
        except ProviderDeadline:
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason="deadline_exceeded",
                limitation=UNAVAILABLE_LIMITATION,
            )
        except ProviderUnavailable as exc:
            if exc.code == "invalid_request":
                return self._cache_and_return_lookup(
                    query,
                    CourtListenerLookupResult(
                        status=CitationStatus.INVALID,
                        query_text=query,
                        reason="invalid_request",
                        limitation=INVALID_LIMITATION,
                    ),
                )
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason=exc.code,
                limitation=UNAVAILABLE_LIMITATION,
            )
        except Exception:
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason="unexpected_error",
                limitation=UNAVAILABLE_LIMITATION,
            )

        if not isinstance(raw_response, list):
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason="invalid_response_structure",
                limitation=UNAVAILABLE_LIMITATION,
            )

        if len(raw_response) == 0:
            return self._cache_and_return_lookup(
                query,
                CourtListenerLookupResult(
                    status=CitationStatus.NOT_FOUND,
                    query_text=query,
                    reason="no_citations_detected",
                    limitation=NOT_FOUND_LIMITATION,
                ),
            )

        item = raw_response[0]
        if not isinstance(item, dict):
            return CourtListenerLookupResult(
                status=CitationStatus.UNAVAILABLE,
                query_text=query,
                reason="invalid_response_item",
                limitation=UNAVAILABLE_LIMITATION,
            )

        provider_status = item.get("status")
        norm_cits = item.get("normalized_citations") or []
        norm_cit = norm_cits[0] if (isinstance(norm_cits, list) and norm_cits) else None
        clusters_raw = item.get("clusters") or []

        if provider_status == 200:
            if len(clusters_raw) == 1 and isinstance(clusters_raw[0], dict):
                cluster = _parse_cluster(clusters_raw[0], norm_cit)
                return self._cache_and_return_lookup(
                    query,
                    CourtListenerLookupResult(
                        status=CitationStatus.VERIFIED,
                        query_text=query,
                        normalized_citation=norm_cit,
                        cluster=cluster,
                        clusters=[cluster],
                        provider_status=200,
                    ),
                )
            if len(clusters_raw) > 1:
                clusters = [
                    _parse_cluster(c, norm_cit)
                    for c in clusters_raw
                    if isinstance(c, dict)
                ]
                return self._cache_and_return_lookup(
                    query,
                    CourtListenerLookupResult(
                        status=CitationStatus.AMBIGUOUS,
                        query_text=query,
                        normalized_citation=norm_cit,
                        clusters=clusters,
                        provider_status=200,
                        reason="multiple_clusters_matched",
                        limitation=AMBIGUOUS_LIMITATION,
                    ),
                )
            return self._cache_and_return_lookup(
                query,
                CourtListenerLookupResult(
                    status=CitationStatus.NOT_FOUND,
                    query_text=query,
                    normalized_citation=norm_cit,
                    provider_status=200,
                    reason="no_clusters_matched",
                    limitation=NOT_FOUND_LIMITATION,
                ),
            )

        if provider_status == 300:
            clusters = [
                _parse_cluster(c, norm_cit)
                for c in clusters_raw
                if isinstance(c, dict)
            ]
            return self._cache_and_return_lookup(
                query,
                CourtListenerLookupResult(
                    status=CitationStatus.AMBIGUOUS,
                    query_text=query,
                    normalized_citation=norm_cit,
                    clusters=clusters,
                    provider_status=300,
                    reason="ambiguous_citation",
                    limitation=AMBIGUOUS_LIMITATION,
                ),
            )

        if provider_status == 400:
            return self._cache_and_return_lookup(
                query,
                CourtListenerLookupResult(
                    status=CitationStatus.INVALID,
                    query_text=query,
                    normalized_citation=norm_cit,
                    provider_status=400,
                    reason="invalid_citation_syntax",
                    limitation=INVALID_LIMITATION,
                ),
            )

        if provider_status == 404:
            return self._cache_and_return_lookup(
                query,
                CourtListenerLookupResult(
                    status=CitationStatus.NOT_FOUND,
                    query_text=query,
                    normalized_citation=norm_cit,
                    provider_status=404,
                    reason="not_found_in_courtlistener_database",
                    limitation=NOT_FOUND_LIMITATION,
                ),
            )

        return CourtListenerLookupResult(
            status=CitationStatus.UNAVAILABLE,
            query_text=query,
            normalized_citation=norm_cit,
            provider_status=provider_status,
            reason=f"provider_status_{provider_status}",
            limitation=UNAVAILABLE_LIMITATION,
        )

    def get_opinion(self, opinion_id: int) -> CourtListenerOpinion:
        """Fetch opinion text and metadata for a single opinion ID."""
        if not isinstance(opinion_id, int) or opinion_id <= 0:
            return CourtListenerOpinion(
                id=opinion_id if isinstance(opinion_id, int) else 0,
                opinion_text_available=False,
                missing_text=True,
            )

        cached = self._cache.get_opinion(opinion_id)
        if cached is not None:
            return cached

        client = self._get_client()
        raw_response = client.request_json("GET", f"/api/rest/v4/opinions/{opinion_id}/")
        if not isinstance(raw_response, dict):
            opinion = CourtListenerOpinion(
                id=opinion_id,
                opinion_text_available=False,
                missing_text=True,
            )
            self._cache.set_opinion(opinion_id, opinion)
            return opinion
        opinion = _parse_opinion(raw_response, opinion_id)
        self._cache.set_opinion(opinion_id, opinion)
        return opinion

    def resolve_cluster_opinion(
        self, cluster: CourtListenerCluster
    ) -> CourtListenerOpinion | None:
        """Select holding opinion for a cluster, avoiding dissents per BUG-004."""
        candidate_ids: list[int] = []
        if cluster.id in cluster.opinion_ids:
            candidate_ids.append(cluster.id)
        for oid in sorted(cluster.opinion_ids):
            if oid not in candidate_ids:
                candidate_ids.append(oid)
        if not candidate_ids and cluster.id > 0:
            candidate_ids.append(cluster.id)

        if not candidate_ids:
            return None

        unclassified_fallback: CourtListenerOpinion | None = None

        for oid in candidate_ids:
            try:
                opinion = self.get_opinion(oid)
            except ProviderUnavailable:
                raise
            except Exception:
                continue

            op_type = (opinion.opinion_type or "").lower().strip()
            if op_type in LEAD_OPINION_TYPES:
                return opinion
            elif op_type in DISSENT_OPINION_TYPES:
                # Per BUG-004: Never use a dissent or concurrence as the holding authority
                continue
            elif not op_type:
                if unclassified_fallback is None:
                    unclassified_fallback = opinion

        return unclassified_fallback

    def resolve_authority(
        self, cluster: CourtListenerCluster
    ) -> CourtListenerResolvedAuthority:
        """Resolve full authority with holding opinion text, metadata, and provenance."""
        cached = self._cache.get_authority(cluster.id)
        if cached is not None:
            return cached

        opinion = self.resolve_cluster_opinion(cluster)
        now = datetime.now(UTC)
        source_url = cluster.source_url or (
            opinion.source_url
            if opinion
            else f"https://www.courtlistener.com/opinion/{cluster.id}/"
        )

        if opinion is not None and opinion.opinion_text_available and opinion.text:
            metadata = {
                "cluster_id": cluster.id,
                "opinion_id": opinion.id,
                "provider_case_name": cluster.case_name,
                "provider_opinion_type": opinion.opinion_type,
                "text_field": opinion.text_field,
                "text_conversion": opinion.text_conversion,
                "raw_sha256": opinion.raw_sha256,
                "characters": len(opinion.text),
                "missing_text": False,
                "provenance": "courtlistener_api_v4",
                "attribution": (
                    "Public US judicial opinion, retrieved from CourtListener / Free Law Project"
                ),
            }
            resolved = CourtListenerResolvedAuthority(
                cluster_id=cluster.id,
                opinion_id=opinion.id,
                case_name=cluster.case_name,
                citation=cluster.citation,
                court=cluster.court,
                year=cluster.year,
                source_url=source_url,
                opinion_text_available=True,
                opinion_text=opinion.text,
                source_sha256=opinion.text_sha256,
                retrieved_at=now,
                source_metadata=metadata,
            )
            self._cache.set_authority(cluster.id, resolved)
            return resolved

        # Opinion text missing or only dissents available
        missing_reason = (
            "dissent_or_concurrence_only"
            if opinion is None and cluster.opinion_ids
            else "opinion_text_empty"
            if opinion is not None
            else "no_opinions_in_cluster"
        )
        metadata = {
            "cluster_id": cluster.id,
            "opinion_id": opinion.id if opinion else None,
            "provider_case_name": cluster.case_name,
            "provider_opinion_type": opinion.opinion_type if opinion else None,
            "missing_text": True,
            "reason": missing_reason,
            "provenance": "courtlistener_api_v4",
            "attribution": (
                "Public US judicial opinion, retrieved from CourtListener / Free Law Project"
            ),
        }
        resolved = CourtListenerResolvedAuthority(
            cluster_id=cluster.id,
            opinion_id=opinion.id if opinion else None,
            case_name=cluster.case_name,
            citation=cluster.citation,
            court=cluster.court,
            year=cluster.year,
            source_url=source_url,
            opinion_text_available=False,
            opinion_text=None,
            source_sha256=None,
            retrieved_at=now,
            source_metadata=metadata,
        )
        self._cache.set_authority(cluster.id, resolved)
        return resolved

    def verify_and_resolve(
        self, citation_text: str
    ) -> tuple[CourtListenerLookupResult, CourtListenerResolvedAuthority | None]:
        """Perform citation verification and retrieve opinion authority if verified."""
        lookup = self.lookup_citation(citation_text)
        if lookup.status == CitationStatus.VERIFIED and lookup.cluster is not None:
            resolved = self.resolve_authority(lookup.cluster)
            return lookup, resolved
        return lookup, None
