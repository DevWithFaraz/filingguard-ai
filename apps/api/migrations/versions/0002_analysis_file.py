"""Persist a unique opaque private-file reference; never a filesystem path."""

import sqlalchemy as sa
from alembic import op

revision = "0002_analysis_file"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analyses", sa.Column("stored_file_id", sa.Uuid(), nullable=True))
    op.create_index("ix_analyses_stored_file_id", "analyses", ["stored_file_id"], unique=True)


def downgrade():
    op.drop_index("ix_analyses_stored_file_id", table_name="analyses")
    op.drop_column("analyses", "stored_file_id")
