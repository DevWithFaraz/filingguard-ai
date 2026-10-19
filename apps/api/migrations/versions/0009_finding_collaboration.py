"""Add finding collaboration comments and disposition metadata."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009_finding_collaboration"
down_revision = "0008_saved_matters"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    op.add_column(
        "findings",
        sa.Column(
            "disposition_metadata",
            JSON_VALUE,
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_table(
        "finding_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("finding_id", sa.Uuid(), nullable=False),
        sa.Column("author_name", sa.String(length=64), nullable=False),
        sa.Column("author_role", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(author_name) >= 1 AND length(author_name) <= 64",
            name=op.f("ck_finding_comments_author_name_valid"),
        ),
        sa.CheckConstraint(
            "length(author_role) >= 1 AND length(author_role) <= 64",
            name=op.f("ck_finding_comments_author_role_valid"),
        ),
        sa.CheckConstraint(
            "length(content) >= 1 AND length(content) <= 2000",
            name=op.f("ck_finding_comments_comment_content_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            ondelete="CASCADE",
            name=op.f("fk_finding_comments_analysis_id_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id", "finding_id"],
            ["findings.analysis_id", "findings.id"],
            ondelete="CASCADE",
            name=op.f("fk_finding_comments_analysis_id_finding_id_findings"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_finding_comments")),
        sa.UniqueConstraint(
            "analysis_id",
            "id",
            name=op.f("uq_finding_comments_analysis_id_id"),
        ),
    )
    op.create_index(
        op.f("ix_finding_comments_finding_id"),
        "finding_comments",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_finding_comments_analysis_id"),
        "finding_comments",
        ["analysis_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_finding_comments_analysis_id"), table_name="finding_comments")
    op.drop_index(op.f("ix_finding_comments_finding_id"), table_name="finding_comments")
    op.drop_table("finding_comments")
    op.drop_column("findings", "disposition_metadata")
