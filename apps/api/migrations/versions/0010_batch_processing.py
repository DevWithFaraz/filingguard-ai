"""Add batch processing tables for multi-filing analysis."""

import sqlalchemy as sa
from alembic import op

revision = "0010_batch_processing"
down_revision = "0009_finding_collaboration"
branch_labels = None
depends_on = None

BATCH_STATUSES = ("queued", "running", "completed", "partial", "cancelled", "failed")


def upgrade():
    op.create_table(
        "batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("total_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(owner_hash) = 64",
            name=op.f("ck_batches_batch_owner_hash_valid"),
        ),
        sa.CheckConstraint(
            "length(name) >= 1 AND length(name) <= 255",
            name=op.f("ck_batches_batch_name_valid"),
        ),
        sa.CheckConstraint(
            f"status IN {BATCH_STATUSES}",
            name=op.f("ck_batches_status_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_batches")),
    )
    op.create_index(op.f("ix_batches_owner_hash"), "batches", ["owner_hash"], unique=False)

    op.create_table(
        "batch_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("document_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"status IN {BATCH_STATUSES}",
            name=op.f("ck_batch_items_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            ondelete="CASCADE",
            name=op.f("fk_batch_items_analysis_id_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batches.id"],
            ondelete="CASCADE",
            name=op.f("fk_batch_items_batch_id_batches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_batch_items")),
    )
    op.create_index(
        op.f("ix_batch_items_batch_id"), "batch_items", ["batch_id"], unique=False
    )
    op.create_index(
        op.f("ix_batch_items_analysis_id"), "batch_items", ["analysis_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_batch_items_analysis_id"), table_name="batch_items")
    op.drop_index(op.f("ix_batch_items_batch_id"), table_name="batch_items")
    op.drop_table("batch_items")
    op.drop_index(op.f("ix_batches_owner_hash"), table_name="batches")
    op.drop_table("batches")
