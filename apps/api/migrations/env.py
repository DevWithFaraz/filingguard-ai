"""No engine at import time, no credential-bearing Alembic config or logging."""

from alembic import context

from filingguard.db.models import Base
from filingguard.db.session import create_db_engine, get_database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests/deployment tooling may supply an already-configured, isolated connection.
    connection = context.config.attributes.get("connection")
    engine = None
    if connection is None:
        engine = create_db_engine()
    try:
        if connection is not None:
            migrate(connection)
        else:
            with engine.connect() as owned_connection:
                migrate(owned_connection)
    finally:
        if engine is not None:
            engine.dispose()


def migrate(connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
