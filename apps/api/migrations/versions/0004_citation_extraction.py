"""Separate local parser provenance from authority verification."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_citation_extraction"
down_revision = "0003_anonymous_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "citations",
        sa.Column(
            "extraction_metadata",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade():
    op.drop_column("citations", "extraction_metadata")
