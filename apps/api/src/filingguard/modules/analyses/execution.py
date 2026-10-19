"""Private JSON stage IPC; only the parent may persist results."""

import json
import math
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from threading import Event, Lock, Thread
from uuid import UUID

from pydantic import Field, model_validator
from pydantic_core import to_jsonable_python
from sqlalchemy import Uuid, inspect

from filingguard.db.models import (
    Analysis,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.db.models.entities import AnalysisOwned
from filingguard.db.session import UTCDateTime
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.schemas import (
    Contract,
    Coverage,
    StageName,
    StageState,
    StageStatus,
)
from filingguard.modules.citations.schemas import (
    CitationExtractionMetadata,
    CitationOccurrence,
    CitationVerificationMetadata,
)
from filingguard.modules.documents.schemas import ExtractedDocument

MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 200
MAX_REVIEW_RECORDS = 1200
RECORD_TYPES = {
    model.__name__: model
    for model in (
        DocumentSegment,
        Authority,
        Citation,
        Claim,
        ClaimAuthorityLink,
        Quote,
        Finding,
        EvidenceRecord,
    )
}
ANALYSIS_FIELDS = (
    "id",
    "document_name",
    "document_sha256",
    "document_snapshot",
    "mode",
    "demo_fixture_id",
    "court_profile_id",
    "ai_used",
    "status",
    "stage_states",
)


class ReviewSegment(Contract):
    id: UUID
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    page_number: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def valid_span(self):
        if self.end <= self.start:
            raise ValueError("Invalid review segment span")
        return self


def validate_segments(analysis: Analysis, segments: tuple[ReviewSegment, ...]) -> None:
    document = ExtractedDocument.model_validate(analysis.document_snapshot)
    if len(segments) != len(document.paragraphs) or len({s.id for s in segments}) != len(segments):
        raise ValueError("Review segment context mismatch")
    if any(
        (segment.start, segment.end, segment.page_number)
        != (paragraph.start, paragraph.end, paragraph.page_number)
        for segment, paragraph in zip(segments, document.paragraphs, strict=True)
    ):
        raise ValueError("Review segment context mismatch")


def citation_anchor(segments: tuple[ReviewSegment, ...], start: int, end: int):
    anchor = next((s for s in segments if s.start <= start < s.end), None)
    if anchor is None:
        raise ValueError("Citation has no original paragraph anchor")
    warnings = []
    if end > anchor.end:
        warnings.append("cross_segment")
    if anchor.page_number is not None and any(
        s.start < end and s.end > start and s.page_number != anchor.page_number for s in segments
    ):
        warnings.append("cross_page")
    return anchor, warnings


def validate_citation_records(
    analysis: Analysis, segments: tuple[ReviewSegment, ...], records: tuple[AnalysisOwned, ...]
) -> None:
    validate_segments(analysis, segments)
    text = analysis.document_snapshot["text"]
    previous_end = -1
    for row in records:
        if type(row) is not Citation or row.analysis_id != analysis.id:
            raise ValueError("Unexpected citation extraction record")
        if not isinstance(row.start_offset, int) or not isinstance(row.end_offset, int):
            raise ValueError("Citation original offsets missing")
        start, end = row.start_offset, row.end_offset
        if not previous_end <= start < end <= len(text) or row.raw_text != text[start:end]:
            raise ValueError("Citation original span mismatch")
        anchor, warnings = citation_anchor(segments, start, end)
        metadata = CitationExtractionMetadata.model_validate(row.extraction_metadata)
        if (
            row.segment_id != anchor.id
            or row.page_number != anchor.page_number
            or metadata.warnings != warnings
        ):
            raise ValueError("Citation original location mismatch")
        previous_end = end


@dataclass(frozen=True)
class ReviewLimits:
    overall_seconds: float = 90
    stage_seconds: float = 30
    max_provider_attempts: int = 60

    def __post_init__(self):
        for value in (self.overall_seconds, self.stage_seconds):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 300:
                raise ValueError("Invalid review deadline")
        if type(self.max_provider_attempts) is not int or not 1 <= self.max_provider_attempts <= 60:
            raise ValueError("Invalid provider attempt limit")


@dataclass(frozen=True)
class StageResult:
    status: StageStatus
    coverage: Coverage = field(default_factory=Coverage)
    reason: str | None = None
    records: tuple[AnalysisOwned, ...] = ()
    updates: tuple[ClaimAuthorityLink, ...] = ()

    def validate(self, stage: StageName) -> None:
        if self.status not in {
            StageStatus.COMPLETED,
            StageStatus.PARTIAL,
            StageStatus.UNAVAILABLE,
            StageStatus.SKIPPED,
        }:
            raise ValueError("Stage runner returned a nonterminal status")
        StageState(
            name=stage,
            status=self.status,
            coverage=self.coverage,
            reason=self.reason,
            applicable=self.status != StageStatus.SKIPPED,
        )
        if self.status == StageStatus.COMPLETED and not self.coverage.complete:
            raise ValueError("A completed stage needs evaluated eligible checks")
        allowed = {
            StageName.CITATIONS: {Citation, Authority, Finding, EvidenceRecord},
            StageName.CLAIMS: {Claim, ClaimAuthorityLink, EvidenceRecord},
            StageName.PROPOSITIONS: {Finding, EvidenceRecord},
            StageName.QUOTES: {Quote, Finding, EvidenceRecord},
            StageName.STATUTES: {Finding, EvidenceRecord},
            StageName.COURT_RULES: {Finding, EvidenceRecord},
            StageName.TABLE_OF_AUTHORITIES: {Finding, EvidenceRecord},
        }.get(stage)
        if allowed is not None and any(type(row) not in allowed for row in self.records):
            raise ValueError("Unexpected record in stage partial-result path")
        if stage == StageName.CITATIONS:
            for row in self.records:
                if type(row) is Citation and row.verification_status != "not_run":
                    receipt = (row.extraction_metadata or {}).get("verification")
                    if receipt is None:
                        raise ValueError("Citation source verdicts require a retrieval receipt")
                    CitationVerificationMetadata.model_validate(receipt)
                    if row.verification_status == "verified" and row.authority_id is None:
                        raise ValueError("Verified source verdicts require an authority")
                elif type(row) is Authority and (
                    row.id is None or row.source != "courtlistener" or row.retrieved_at is None
                ):
                    raise ValueError("Authority source verdicts require retrieval provenance")
        if self.status != StageStatus.COMPLETED and self.records:
            if stage in {
                StageName.CLAIMS,
                StageName.PROPOSITIONS,
                StageName.QUOTES,
                StageName.STATUTES,
                StageName.COURT_RULES,
                StageName.TABLE_OF_AUTHORITIES,
            }:
                if self.status != StageStatus.PARTIAL:
                    raise ValueError("Only terminal partial stages may preserve results")
            elif stage == StageName.CITATIONS and any(
                type(r) is Authority or (type(r) is Citation and r.verification_status != "not_run")
                for r in self.records
            ):
                if self.status != StageStatus.PARTIAL:
                    raise ValueError("Only partial verification may preserve source results")
                if any(
                    type(r) not in {Authority, Citation, Finding, EvidenceRecord}
                    for r in self.records
                ):
                    raise ValueError("Unexpected partial verification record")
            else:
                self._validate_partial_extraction(stage)
        limit = (
            MAX_REVIEW_RECORDS
            if stage
            in {
                StageName.CITATIONS,
                StageName.CLAIMS,
                StageName.PROPOSITIONS,
                StageName.QUOTES,
                StageName.STATUTES,
                StageName.COURT_RULES,
                StageName.TABLE_OF_AUTHORITIES,
            }
            else MAX_RECORDS
        )
        if len(self.records) > limit:
            raise ValueError("Stage record limit exceeded")
        if len(self.updates) > 200 or (self.updates and stage != StageName.PROPOSITIONS):
            raise ValueError("Only proposition link verdicts may be updated")
        if self.status not in {StageStatus.PARTIAL, StageStatus.COMPLETED} and self.updates:
            raise ValueError("Failed stages cannot update verdicts")

    def _validate_partial_extraction(self, stage: StageName) -> None:
        if (
            stage != StageName.CITATIONS
            or self.status != StageStatus.PARTIAL
            or self.coverage.evaluated != 0
            or self.coverage.pending != 0
            or self.coverage.eligible < len(self.records)
            or self.coverage.unavailable != self.coverage.eligible
        ):
            raise ValueError("Incomplete stage output needs a dedicated partial-result path")
        for row in self.records:
            if (
                type(row) is not Citation
                or row.verification_status != "not_run"
                or row.authority_id is not None
                or row.segment_id is None
            ):
                raise ValueError("Partial citation extraction cannot assert source verdicts")
            occurrence = CitationOccurrence(
                raw_text=row.raw_text,
                normalized_text=row.normalized_text,
                start=row.start_offset,
                end=row.end_offset,
                extraction=row.extraction_metadata,
            )
            if occurrence.normalized_text is not None and (
                occurrence.extraction.kind != "full_case"
                or occurrence.extraction.support != "recognized"
            ):
                raise ValueError("Unresolved citations cannot have a normalized authority")


CONTEXT_TYPES = {
    "citations": Citation,
    "authorities": Authority,
    "claims": Claim,
    "links": ClaimAuthorityLink,
}


def validate_stage_context(result, analysis, stage, segments, context):
    """The parent rechecks new output against its own persisted snapshot and prior rows."""
    if not result.records and not result.updates:
        return
    if stage not in {
        StageName.CITATIONS,
        StageName.CLAIMS,
        StageName.PROPOSITIONS,
        StageName.QUOTES,
    }:
        return
    allowed = {
        StageName.CITATIONS: {Citation, Authority, Finding, EvidenceRecord},
        StageName.CLAIMS: {Claim, ClaimAuthorityLink, EvidenceRecord},
        StageName.PROPOSITIONS: {Finding, EvidenceRecord},
        StageName.QUOTES: {Quote, Finding, EvidenceRecord},
    }[stage]
    caps = {
        Citation: 200,
        Authority: 25,
        Claim: 100,
        ClaimAuthorityLink: 200,
        Quote: 50,
        Finding: 400,
        EvidenceRecord: 400,
    }
    if any(type(row) not in allowed or row.analysis_id != analysis.id for row in result.records):
        raise ValueError("Unexpected stage record or owner")
    if any(sum(type(r) is model for r in result.records) > caps[model] for model in allowed):
        raise ValueError("Stage entity cap exceeded")
    if len({r.id for r in result.records}) != len(result.records):
        raise ValueError("Duplicate stage identity")
    text = analysis.document_snapshot["text"]
    prior = {name: {r.id: r for r in rows} for name, rows in context.items()}
    new = {model: {r.id: r for r in result.records if type(r) is model} for model in allowed}
    authorities = {**prior.get("authorities", {}), **new.get(Authority, {})}
    citations = {**prior.get("citations", {}), **new.get(Citation, {})}
    claims = {**prior.get("claims", {}), **new.get(Claim, {})}
    quotes = new.get(Quote, {})
    findings = new.get(Finding, {})
    links = {**prior.get("links", {}), **new.get(ClaimAuthorityLink, {})}
    relations = {
        "citation_id": citations,
        "authority_id": authorities,
        "claim_id": claims,
        "quote_id": quotes,
    }
    for row in (*findings.values(), *new.get(EvidenceRecord, {}).values()):
        for field_name, known in relations.items():
            identity = getattr(row, field_name)
            if identity is not None and identity not in known:
                raise ValueError("Finding or evidence relation is outside stage context")
        citation = citations.get(row.citation_id)
        if row.authority_id is not None and (
            citation is None or row.authority_id != citation.authority_id
        ):
            raise ValueError("Finding or evidence authority does not match citation")
        quote = quotes.get(row.quote_id)
        if quote is not None and row.citation_id != quote.citation_id:
            raise ValueError("Finding or evidence quote does not match citation")
        if (
            row.claim_id is not None
            and row.citation_id is not None
            and not any(
                link.claim_id == row.claim_id
                and link.citation_id == row.citation_id
                and (row.authority_id is None or link.authority_id == row.authority_id)
                for link in links.values()
            )
        ):
            raise ValueError("Finding or evidence claim has no matching citation link")
    for row in new.get(EvidenceRecord, {}).values():
        if row.finding_id is not None:
            finding = findings.get(row.finding_id)
            if finding is None or any(
                getattr(finding, field_name) is not None
                and getattr(row, field_name) != getattr(finding, field_name)
                for field_name in relations
                if field_name != "authority_id"
                or row.source_type != "document"
                or row.authority_id is not None
            ):
                raise ValueError("Evidence does not belong to its finding relations")
    if stage == StageName.CITATIONS:
        rows = tuple(sorted(new[Citation].values(), key=lambda r: r.start_offset))
        validate_citation_records(analysis, segments, rows)
        for row in rows:
            metadata = CitationExtractionMetadata.model_validate(row.extraction_metadata)
            if row.verification_status == "verified":
                if row.authority_id not in authorities or metadata.support != "recognized":
                    raise ValueError("Verified citation needs a recognized authority")
            elif row.authority_id is not None:
                raise ValueError("Unverified citation cannot assert an authority")
            if row.verification_status != "not_run" and metadata.verification is None:
                raise ValueError("Citation verdict needs a retrieval receipt")
    for row in new.get(Authority, {}).values():
        if row.source != "courtlistener" or row.retrieved_at is None:
            raise ValueError("Authority retrieval provenance missing")
        if row.opinion_text_available:
            if (
                not row.opinion_text
                or sha256(row.opinion_text.encode()).hexdigest() != row.source_sha256
            ):
                raise ValueError("Authority snapshot hash mismatch")
        elif row.opinion_text is not None or row.source_sha256 is not None:
            raise ValueError("Unavailable source cannot contain text")
    for model, text_field in ((Claim, "text"), (Quote, "quote_text")):
        for row in new.get(model, {}).values():
            if not isinstance(row.start_offset, int) or not isinstance(row.end_offset, int):
                raise ValueError("Original span missing")
            if not 0 <= row.start_offset < row.end_offset <= len(text):
                raise ValueError("Original span outside filing")
            if text[row.start_offset : row.end_offset] != getattr(row, text_field):
                raise ValueError("Original excerpt mismatch")
            anchor, _ = citation_anchor(segments, row.start_offset, row.end_offset)
            if row.segment_id != anchor.id or row.page_number != anchor.page_number:
                raise ValueError("Original anchor mismatch")
    for row in new.get(ClaimAuthorityLink, {}).values():
        citation = citations.get(row.citation_id)
        if (
            row.claim_id not in claims
            or citation is None
            or row.authority_id != citation.authority_id
        ):
            raise ValueError("Claim link provenance mismatch")
        if row.support_status != "not_run":
            raise ValueError("Claim extraction cannot assert semantic support")
    for row in new.get(Quote, {}).values():
        if row.citation_id is not None and row.citation_id not in citations:
            raise ValueError("Quote citation provenance mismatch")
    for row in new.get(EvidenceRecord, {}).values():
        if (
            not row.snapshot_text
            or sha256(row.snapshot_text.encode()).hexdigest() != row.source_sha256
        ):
            raise ValueError("Evidence snapshot mismatch")
        if (
            not isinstance(row.source_start_offset, int)
            or not isinstance(row.source_end_offset, int)
            or not 0 <= row.source_start_offset < row.source_end_offset <= len(row.snapshot_text)
            or row.snapshot_text[row.source_start_offset : row.source_end_offset] != row.excerpt
        ):
            raise ValueError("Evidence passage mismatch")
        if row.source_type == "document" and row.snapshot_text != text:
            raise ValueError("Evidence document substitution")
        if row.source_type in {"opinion_text", "ai_analysis"}:
            authority = authorities.get(row.authority_id)
            if authority is None or row.snapshot_text != authority.opinion_text:
                raise ValueError("Evidence source substitution")
            if row.source_sha256 != authority.source_sha256:
                raise ValueError("Evidence retrieval mismatch")
        if row.source_type == "ai_analysis" and (not row.model_version or not row.prompt_version):
            raise ValueError("Model provenance missing")
    for row in result.updates:
        original = prior.get("links", {}).get(row.id)
        if (
            original is None
            or row.analysis_id != analysis.id
            or any(
                getattr(row, k) != getattr(original, k)
                for k in ("claim_id", "citation_id", "authority_id")
            )
        ):
            raise ValueError("Proposition update provenance mismatch")


StageRunner = Callable[[Analysis, ProviderBudget], StageResult] | StageResult


class StageExecutionError(Exception):
    def __init__(self, code: str):
        reasons = {
            "deadline": (StageStatus.UNAVAILABLE, "Review work deadline exceeded"),
            "shutdown": (StageStatus.INTERRUPTED, "Review stopped during shutdown"),
            "provider": (
                StageStatus.UNAVAILABLE,
                "External provider unavailable or budget exhausted",
            ),
            "worker": (StageStatus.UNAVAILABLE, "Contained review worker unavailable"),
            "limit": (StageStatus.UNAVAILABLE, "Review stage exceeded output or resource limits"),
            "failed": (StageStatus.FAILED, "Review stage failed"),
        }
        self.status, self.reason = reasons.get(code, reasons["failed"])
        super().__init__(self.reason)


def runner_name(runner: StageRunner) -> str:
    if not callable(runner) or not hasattr(runner, "__qualname__"):
        raise ValueError("Stage runner must be an importable module-level function")
    if "<" in runner.__qualname__ or "." in runner.__qualname__ or runner.__module__ == "__main__":
        raise ValueError("Stage runner must be an importable module-level function")
    return f"{runner.__module__}:{runner.__qualname__}"


def row_to_wire(row) -> dict:
    values = {
        attr.key: row.__dict__[attr.key]
        for attr in inspect(type(row)).column_attrs
        if attr.key in row.__dict__
    }
    return to_jsonable_python(values)


def row_from_wire(model, values: dict):
    columns = {attr.key: attr.columns[0] for attr in inspect(model).column_attrs}
    if not isinstance(values, dict) or values.keys() - columns.keys():
        raise ValueError("Unexpected stage record fields")
    decoded = dict(values)
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(columns[key].type, Uuid):
            decoded[key] = UUID(value)
        elif isinstance(columns[key].type, UTCDateTime):
            decoded[key] = datetime.fromisoformat(value)
    return model(**decoded)


def result_to_wire(result: StageResult) -> dict:
    records = []
    for row in result.records:
        if (
            type(row).__name__ not in RECORD_TYPES
            or type(row) is not RECORD_TYPES[type(row).__name__]
        ):
            raise ValueError("Unexpected stage record type")
        records.append({"type": type(row).__name__, "values": row_to_wire(row)})
    return {
        "status": result.status.value,
        "coverage": result.coverage.model_dump(),
        "reason": result.reason,
        "records": records,
        "updates": [row_to_wire(row) for row in result.updates],
    }


def result_from_wire(value: dict, analysis_id: UUID) -> StageResult:
    if len(value["records"]) > MAX_REVIEW_RECORDS:
        raise ValueError("Stage record limit exceeded")
    records = tuple(
        row_from_wire(RECORD_TYPES[row["type"]], row["values"]) for row in value["records"]
    )
    if any(row.analysis_id != analysis_id for row in records):
        raise ValueError("Stage result ownership mismatch")
    return StageResult(
        status=StageStatus(value["status"]),
        coverage=Coverage.model_validate(value["coverage"]),
        reason=value["reason"],
        records=records,
        updates=tuple(row_from_wire(ClaimAuthorityLink, r) for r in value.get("updates", [])),
    )


def execute_stage(
    runner: StageRunner,
    analysis: Analysis,
    stage: StageName,
    budget: ProviderBudget,
    *,
    stage_seconds: float,
    stop: Event,
    segments: tuple[ReviewSegment, ...] = (),
    context: dict[str, tuple[AnalysisOwned, ...]] | None = None,
    credentials: dict[str, str] | None = None,
) -> StageResult:
    deadline = min(budget.deadline, time.monotonic() + stage_seconds)
    if stop.is_set():
        raise StageExecutionError("shutdown")
    if deadline <= time.monotonic():
        raise StageExecutionError("deadline")
    if isinstance(runner, StageResult):
        if runner.status not in {StageStatus.UNAVAILABLE, StageStatus.SKIPPED} or runner.records:
            raise StageExecutionError("failed")
        runner.validate(stage)
        return runner
    snapshot = analysis.document_snapshot
    if not snapshot or not isinstance(snapshot.get("text"), str) or len(snapshot["text"]) > 100000:
        raise StageExecutionError("limit")
    if segments:
        validate_segments(analysis, segments)
    attempts_left = budget.max_attempts - budget.attempts_used
    payload = json.dumps(
        {
            "runner": runner_name(runner),
            "stage": stage.value,
            "analysis": to_jsonable_python(
                {key: getattr(analysis, key) for key in ANALYSIS_FIELDS}
            ),
            "deadline": deadline,
            "attempts_left": attempts_left,
            "segments": [s.model_dump(mode="json") for s in segments],
            "context": {
                key: [row_to_wire(row) for row in rows] for key, rows in (context or {}).items()
            },
            "credentials": credentials or {},
        },
        ensure_ascii=False,
        allow_nan=False,
    ).encode()
    if len(payload) > MAX_INPUT_BYTES:
        raise StageExecutionError("limit")
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
    }
    env["PYTHONPATH"] = os.pathsep.join(path for path in sys.path if path)
    job = None
    process = None
    accounted = False
    finished = Event()
    terminate_lock = Lock()
    terminated = False
    watcher = None

    def terminate_tree():
        nonlocal terminated
        with terminate_lock:
            if terminated or process is None:
                return
            terminated = True
            if job is not None:
                job.close()
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if process.poll() is None:
                process.kill()

    def watch_deadline():
        # Windows communicate() can block writing stdin before honoring its timeout.
        while not finished.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0 or stop.is_set():
                terminate_tree()
                return
            finished.wait(min(0.05, remaining))

    try:
        # Bypass the Windows venv redirector: no interpreter can spawn outside the job
        # before assignment. The private import path still includes venv dependencies.
        interpreter = sys._base_executable if os.name == "nt" else sys.executable
        process = subprocess.Popen(
            [interpreter, "-m", "filingguard.modules.analyses.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if os.name == "nt":
            from filingguard.modules.documents.windows_job import WindowsJob

            job = WindowsJob(int(process._handle), memory_mb=384, max_processes=2)
        watcher = Thread(target=watch_deadline, daemon=True, name="filingguard-stage-deadline")
        watcher.start()
        # Keep input delivery in one call. On POSIX, retrying communicate(None)
        # after a short timeout can leave a partly written stdin pipe open forever.
        # The watcher independently kills the process tree on shutdown or cutoff,
        # including Windows' potentially blocking stdin write.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise StageExecutionError("deadline")
        try:
            output, _ = process.communicate(payload, timeout=remaining)
        except subprocess.TimeoutExpired:
            raise StageExecutionError("deadline") from None
        if stop.is_set():
            raise StageExecutionError("shutdown")
        if time.monotonic() >= deadline:
            raise StageExecutionError("deadline")
        if process.returncode or len(output) > MAX_OUTPUT_BYTES:
            raise StageExecutionError("limit")
        envelope = json.loads(output)
        used = envelope["attempts_used"]
        if type(used) is not int or not 0 <= used <= attempts_left:
            raise StageExecutionError("limit")
        budget.attempts_used += used
        accounted = True
        if "error" in envelope:
            raise StageExecutionError(envelope["error"])
        result = result_from_wire(envelope["result"], analysis.id)
        result.validate(stage)
        validate_stage_context(result, analysis, stage, segments, context or {})
        return result
    except StageExecutionError:
        raise
    except Exception:
        raise StageExecutionError("worker") from None
    finally:
        finished.set()
        if watcher is not None:
            watcher.join()
        if process is not None and not accounted:
            # A killed worker cannot report attempts: do not spend an unknown quota again.
            budget.attempts_used = budget.max_attempts
        if process is not None:
            terminate_tree()
            process.communicate()
