"""Allow Table of Authorities finding types."""

from alembic import op

revision = "0005_table_of_authorities"
down_revision = "0004_citation_extraction"
branch_labels = None
depends_on = None

PRIOR = ("citation", "claim_support", "quote", "privacy", "court_rule", "system")
CURRENT = (*PRIOR, "table_of_authorities")


def _check(values: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{value}'" for value in values)
    return f"type IN ({allowed})"


def _replace_type_check(values: tuple[str, ...]) -> None:
    context = op.get_context()
    dialect = context.dialect.name
    expression = _check(values)
    if dialect == "sqlite" and context.as_sql:
        # SQLite table rebuild cannot be reflected in --sql mode.
        op.execute("SELECT 1")
        return
    if dialect == "sqlite":
        with op.batch_alter_table("findings") as batch:
            batch.drop_constraint("type_valid", type_="check")
            batch.create_check_constraint("type_valid", expression)
        return
    op.execute("ALTER TABLE findings DROP CONSTRAINT ck_findings_type_valid")
    op.execute(f"ALTER TABLE findings ADD CONSTRAINT ck_findings_type_valid CHECK ({expression})")


def upgrade():
    _replace_type_check(CURRENT)


def downgrade():
    op.execute("UPDATE findings SET type = 'citation' WHERE type = 'table_of_authorities'")
    _replace_type_check(PRIOR)
