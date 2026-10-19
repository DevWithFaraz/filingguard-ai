"""Optional local identity records bound to anonymous owner_hash."""

import sqlalchemy as sa
from alembic import op

revision = "0007_local_identities"
down_revision = "0006_claim_corrections"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "local_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("secret_hash", sa.String(length=255), nullable=False),
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(owner_hash) = 64",
            name=op.f("ck_local_identities_owner_hash_valid"),
        ),
        sa.CheckConstraint(
            "length(username) >= 3 AND length(username) <= 32",
            name=op.f("ck_local_identities_username_valid"),
        ),
        sa.CheckConstraint(
            "length(secret_hash) >= 32",
            name=op.f("ck_local_identities_secret_hash_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_local_identities")),
        sa.UniqueConstraint("username", name=op.f("uq_local_identities_username")),
        sa.UniqueConstraint("owner_hash", name=op.f("uq_local_identities_owner_hash")),
    )
    op.create_table(
        "identity_sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(token_hash) = 64",
            name=op.f("ck_identity_sessions_token_hash_valid"),
        ),
        sa.CheckConstraint(
            "length(owner_hash) = 64",
            name=op.f("ck_identity_sessions_owner_hash_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_hash"],
            ["local_identities.owner_hash"],
            ondelete="CASCADE",
            name=op.f("fk_identity_sessions_owner_hash_local_identities"),
        ),
        sa.PrimaryKeyConstraint("token_hash", name=op.f("pk_identity_sessions")),
    )
    op.create_index("ix_identity_sessions_expires_at", "identity_sessions", ["expires_at"])
    op.create_index("ix_identity_sessions_owner_hash", "identity_sessions", ["owner_hash"])


def downgrade():
    op.drop_index("ix_identity_sessions_owner_hash", table_name="identity_sessions")
    op.drop_index("ix_identity_sessions_expires_at", table_name="identity_sessions")
    op.drop_table("identity_sessions")
    op.drop_table("local_identities")
