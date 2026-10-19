"""Store claim correction history without rewriting original extraction."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006_claim_corrections"
down_revision = "0005_table_of_authorities"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "claims",
        sa.Column(
            "correction_history",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade():
    op.drop_column("claims", "correction_history")
