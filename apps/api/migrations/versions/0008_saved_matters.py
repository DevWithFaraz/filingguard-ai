"""Add saved matters table and optional matter_id on analyses."""

import sqlalchemy as sa
from alembic import op

revision = "0008_saved_matters"
down_revision = "0007_local_identities"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "matters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("case_number", sa.String(length=64), nullable=True),
        sa.Column("client_id", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
            name=op.f("ck_matters_matter_owner_hash_valid"),
        ),
        sa.CheckConstraint(
            "length(name) >= 1 AND length(name) <= 255",
            name=op.f("ck_matters_matter_name_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matters")),
        sa.UniqueConstraint("owner_hash", "name", name=op.f("uq_matters_owner_hash_name")),
    )
    op.create_index(op.f("ix_matters_owner_hash"), "matters", ["owner_hash"], unique=False)
    op.add_column("analyses", sa.Column("matter_id", sa.Uuid(), nullable=True))
    op.create_index("ix_analyses_matter_id", "analyses", ["matter_id"], unique=False)
    if op.get_context().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_analyses_matter_id_matters",
            "analyses",
            "matters",
            ["matter_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    if op.get_context().dialect.name != "sqlite":
        op.drop_constraint("fk_analyses_matter_id_matters", "analyses", type_="foreignkey")
    op.drop_index("ix_analyses_matter_id", table_name="analyses")
    op.drop_column("analyses", "matter_id")
    op.drop_index(op.f("ix_matters_owner_hash"), table_name="matters")
    op.drop_table("matters")
