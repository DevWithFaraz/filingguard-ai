"""Persist only anonymous bearer hashes and server expiry."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_anonymous_sessions"
down_revision = "0002_analysis_file"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "analyses",
        sa.Column(
            "document_snapshot", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True
        ),
    )
    op.create_table(
        "anonymous_sessions",
        sa.Column("owner_hash", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(owner_hash) = 64", name=op.f("ck_anonymous_sessions_owner_hash_valid")
        ),
    )
    op.create_index("ix_anonymous_sessions_expires_at", "anonymous_sessions", ["expires_at"])


def downgrade():
    op.drop_table("anonymous_sessions")
    op.drop_column("analyses", "document_snapshot")
