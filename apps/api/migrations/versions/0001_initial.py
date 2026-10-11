"""Nine analysis-owned entities with scoped references and independent evidence.

Revision ID: 0001_initial
Revises: None
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _json():
    return sa.JSON().with_variant(JSONB(), "postgresql")


def _status(column, values):
    allowed = ", ".join(f"'{value}'" for value in values)
    return column + "_valid", f"{column} IN ({allowed})"


def _offsets(start="start_offset", end="end_offset"):
    return start + "_valid", (
        f"({start} IS NULL AND {end} IS NULL) OR "
        f"({start} IS NOT NULL AND {end} IS NOT NULL AND {start} >= 0 AND {end} >= {start})"
    )


def _confidence(column="confidence"):
    return column + "_valid", f"{column} >= 0 AND {column} <= 1"


def _owned(table, columns, *, references=(), checks=(), unique=(), location=False):
    constraints = [
        sa.PrimaryKeyConstraint("id", name=f"pk_{table}"),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            ondelete="CASCADE",
            name=f"fk_{table}_analysis_id_analyses",
        ),
        sa.UniqueConstraint("analysis_id", "id", name=f"uq_{table}_analysis_id_id"),
    ]
    for column, target in references:
        constraints.append(
            sa.ForeignKeyConstraint(
                ["analysis_id", column],
                [f"{target}.analysis_id", f"{target}.id"],
                ondelete="CASCADE",
                name=f"fk_{table}_analysis_id_{column}_{target}",
            )
        )
    for name, expression in checks:
        constraints.append(sa.CheckConstraint(expression, name=op.f(f"ck_{table}_{name}")))
    for fields in unique:
        constraints.append(
            sa.UniqueConstraint(
                *fields,
                name=op.f(f"uq_{table}_{'_'.join(fields)}"),
            )
        )
    if location:
        columns += [
            sa.Column("page_number", sa.Integer()),
            sa.Column("start_offset", sa.Integer()),
            sa.Column("end_offset", sa.Integer()),
        ]
    op.create_table(
        table,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        *columns,
        *constraints,
    )
    op.create_index(f"ix_{table}_analysis_id", table, ["analysis_id"])


def upgrade() -> None:
    # This schema snapshot is intentionally independent of future application models.
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("document_sha256", sa.String(64), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default="live"),
        sa.Column("demo_fixture_id", sa.String(255)),
        sa.Column("court_profile_id", sa.String(255)),
        sa.Column("ai_used", sa.Boolean()),
        sa.Column("status", sa.String(32), nullable=False, server_default="not_run"),
        sa.Column("stage_states", _json(), nullable=False, server_default="{}"),
        sa.Column("overall_score", sa.Integer()),
        sa.Column("risk_level", sa.String(32)),
        sa.PrimaryKeyConstraint("id", name="pk_analyses"),
        *[
            sa.CheckConstraint(expression, name=op.f(f"ck_analyses_{name}"))
            for name, expression in (
                _status(
                    "status",
                    (
                        "not_run",
                        "queued",
                        "running",
                        "completed",
                        "partial",
                        "failed",
                        "interrupted",
                    ),
                ),
                _status("mode", ("live", "demo")),
                _status("risk_level", ("ready_for_review", "needs_review", "high_risk")),
                ("score_valid", "overall_score >= 0 AND overall_score <= 100"),
                ("risk_requires_score", "risk_level IS NULL OR overall_score IS NOT NULL"),
                ("owner_hash_valid", "length(owner_hash) = 64"),
                ("document_hash_valid", "length(document_sha256) = 64"),
                ("expiry_valid", "expires_at > created_at"),
                (
                    "demo_identity_valid",
                    "(mode = 'live' AND demo_fixture_id IS NULL) OR "
                    "(mode = 'demo' AND demo_fixture_id IS NOT NULL "
                    "AND length(demo_fixture_id) > 0)",
                ),
            )
        ],
    )
    op.create_index("ix_analyses_owner_hash", "analyses", ["owner_hash"])
    op.create_index("ix_analyses_expires_at", "analyses", ["expires_at"])
    _owned(
        "document_segments",
        [
            sa.Column("paragraph_index", sa.Integer(), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
        ],
        location=True,
        unique=[("analysis_id", "paragraph_index")],
        checks=[
            _offsets(),
            ("page_number_valid", "page_number >= 1"),
            ("paragraph_index_valid", "paragraph_index >= 0"),
        ],
    )
    _owned(
        "authorities",
        [
            sa.Column("source", sa.String(80), nullable=False),
            sa.Column("external_id", sa.String(255)),
            sa.Column("case_name", sa.Text()),
            sa.Column("citation", sa.String(255)),
            sa.Column("court", sa.String(255)),
            sa.Column("year", sa.Integer()),
            sa.Column("source_url", sa.Text()),
            sa.Column(
                "opinion_text_available", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("opinion_text", sa.Text()),
            sa.Column("source_sha256", sa.String(64)),
            sa.Column("retrieved_at", sa.DateTime(timezone=True)),
            sa.Column("source_metadata", _json(), nullable=False, server_default="{}"),
        ],
        unique=[("analysis_id", "source", "external_id")],
        checks=[
            ("source_hash_valid", "length(source_sha256) = 64"),
        ],
    )
    _owned(
        "citations",
        [
            sa.Column("raw_text", sa.Text(), nullable=False),
            sa.Column("normalized_text", sa.Text()),
            sa.Column("segment_id", sa.Uuid(), nullable=False),
            sa.Column("authority_id", sa.Uuid()),
            sa.Column(
                "verification_status", sa.String(32), nullable=False, server_default="not_run"
            ),
        ],
        location=True,
        references=[
            ("segment_id", "document_segments"),
            ("authority_id", "authorities"),
        ],
        checks=[
            _offsets(),
            ("page_number_valid", "page_number >= 1"),
            _status(
                "verification_status",
                (
                    "not_run",
                    "verified",
                    "not_found",
                    "invalid",
                    "ambiguous",
                    "unavailable",
                ),
            ),
        ],
    )
    _owned(
        "claims",
        [
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("segment_id", sa.Uuid(), nullable=False),
            sa.Column("extraction_method", sa.String(32), nullable=False),
            sa.Column("confidence", sa.Float()),
            sa.Column("model_version", sa.String(255)),
            sa.Column("prompt_version", sa.String(255)),
        ],
        location=True,
        references=[("segment_id", "document_segments")],
        checks=[
            _offsets(),
            _confidence(),
            ("page_number_valid", "page_number >= 1"),
            _status("extraction_method", ("heuristic", "ai")),
        ],
    )
    _owned(
        "claim_authority_links",
        [
            sa.Column("claim_id", sa.Uuid(), nullable=False),
            sa.Column("citation_id", sa.Uuid(), nullable=False),
            sa.Column("authority_id", sa.Uuid()),
            sa.Column("support_status", sa.String(32), nullable=False, server_default="not_run"),
            sa.Column("confidence", sa.Float()),
            sa.Column("explanation", sa.Text()),
        ],
        references=[
            ("claim_id", "claims"),
            ("citation_id", "citations"),
            ("authority_id", "authorities"),
        ],
        unique=[("analysis_id", "claim_id", "citation_id", "authority_id")],
        checks=[
            _confidence(),
            _status(
                "support_status",
                (
                    "not_run",
                    "supported",
                    "partially_supported",
                    "unclear",
                    "misrepresented",
                    "insufficient_source",
                    "unavailable",
                ),
            ),
        ],
    )
    _owned(
        "quotes",
        [
            sa.Column("quote_text", sa.Text(), nullable=False),
            sa.Column("segment_id", sa.Uuid(), nullable=False),
            sa.Column("citation_id", sa.Uuid()),
            sa.Column("match_status", sa.String(32), nullable=False, server_default="not_run"),
            sa.Column("similarity", sa.Float()),
            sa.Column("closest_passage", sa.Text()),
        ],
        location=True,
        references=[
            ("segment_id", "document_segments"),
            ("citation_id", "citations"),
        ],
        checks=[
            _offsets(),
            _confidence("similarity"),
            ("page_number_valid", "page_number >= 1"),
            _status(
                "match_status",
                (
                    "not_run",
                    "exact",
                    "normalized",
                    "close",
                    "not_found",
                    "source_unavailable",
                ),
            ),
        ],
    )
    _owned(
        "findings",
        [
            sa.Column("type", sa.String(32), nullable=False),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("stage", sa.String(80)),
            sa.Column("segment_id", sa.Uuid()),
            sa.Column("citation_id", sa.Uuid()),
            sa.Column("authority_id", sa.Uuid()),
            sa.Column("claim_id", sa.Uuid()),
            sa.Column("quote_id", sa.Uuid()),
            sa.Column("rule_id", sa.String(255)),
            sa.Column("document_excerpt", sa.Text()),
            sa.Column("confidence", sa.Float()),
            sa.Column("ai_assisted", sa.Boolean(), nullable=False, server_default=sa.false()),
        ],
        location=True,
        references=[
            ("segment_id", "document_segments"),
            ("citation_id", "citations"),
            ("authority_id", "authorities"),
            ("claim_id", "claims"),
            ("quote_id", "quotes"),
        ],
        checks=[
            _offsets(),
            _confidence(),
            ("page_number_valid", "page_number >= 1"),
            _status(
                "type", ("citation", "claim_support", "quote", "privacy", "court_rule", "system")
            ),
            _status("severity", ("info", "low", "medium", "high", "critical")),
            _status("status", ("open", "reviewed", "resolved")),
        ],
    )
    _owned(
        "evidence_records",
        [
            sa.Column("finding_id", sa.Uuid()),
            sa.Column("segment_id", sa.Uuid()),
            sa.Column("citation_id", sa.Uuid()),
            sa.Column("authority_id", sa.Uuid()),
            sa.Column("claim_id", sa.Uuid()),
            sa.Column("quote_id", sa.Uuid()),
            sa.Column("source_type", sa.String(32), nullable=False),
            sa.Column("source_label", sa.String(255), nullable=False),
            sa.Column("excerpt", sa.Text(), nullable=False),
            sa.Column("snapshot_text", sa.Text()),
            sa.Column("source_url", sa.Text()),
            sa.Column("source_sha256", sa.String(64)),
            sa.Column("retrieved_at", sa.DateTime(timezone=True)),
            sa.Column("source_start_offset", sa.Integer()),
            sa.Column("source_end_offset", sa.Integer()),
            sa.Column("method", sa.String(80), nullable=False),
            sa.Column("method_version", sa.String(255), nullable=False),
            sa.Column("model_version", sa.String(255)),
            sa.Column("prompt_version", sa.String(255)),
            sa.Column("source_metadata", _json(), nullable=False, server_default="{}"),
        ],
        location=True,
        references=[
            ("finding_id", "findings"),
            ("segment_id", "document_segments"),
            ("citation_id", "citations"),
            ("authority_id", "authorities"),
            ("claim_id", "claims"),
            ("quote_id", "quotes"),
        ],
        checks=[
            _offsets(),
            _offsets("source_start_offset", "source_end_offset"),
            ("page_number_valid", "page_number >= 1"),
            ("source_hash_valid", "length(source_sha256) = 64"),
            _status("source_type", ("document", "api", "opinion_text", "ai_analysis", "rule")),
        ],
    )
    op.create_index("ix_evidence_records_finding_id", "evidence_records", ["finding_id"])


def downgrade() -> None:
    for table in (
        "evidence_records",
        "findings",
        "quotes",
        "claim_authority_links",
        "claims",
        "citations",
        "authorities",
        "document_segments",
        "analyses",
    ):
        op.drop_table(table)
