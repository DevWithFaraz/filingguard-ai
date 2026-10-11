"""Explicit, lazy synchronous database setup for thread-offloaded units of work."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from pydantic import SecretStr
from sqlalchemy import DateTime, Engine, create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from filingguard.core.config import Settings


class DatabaseConfigurationError(ValueError):
    """Configuration error whose message never contains connection credentials."""


class _DatabaseSettings(Settings):
    database_url: SecretStr


class UTCDateTime(TypeDecorator[datetime]):
    """Reject naive inputs and restore UTC awareness after SQLite round trips."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Database timestamps must be timezone-aware")
        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def get_database_url(value: str | URL | None = None) -> URL:
    """Read Settings/env/dotenv privately, with no URL in configuration errors."""
    try:
        if value is None:
            value = _DatabaseSettings().database_url.get_secret_value()
        url = make_url(value)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+psycopg")
        if url.get_backend_name() not in {"sqlite", "postgresql"}:
            raise ValueError("Unsupported database dialect")
        return url
    except (ValueError, TypeError, ArgumentError):
        raise DatabaseConfigurationError("DATABASE_URL is missing or invalid") from None


def create_db_engine(url: str | URL | None = None) -> Engine:
    """Create, but do not connect, an engine. The caller owns disposal."""
    database_url = get_database_url(url)
    options = {"echo": False, "hide_parameters": True, "pool_pre_ping": True}
    if database_url.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False}
        if database_url.database in {None, "", ":memory:"}:
            options["poolclass"] = StaticPool
    else:
        options["connect_args"] = {
            "connect_timeout": 5,
            "options": "-c statement_timeout=10000 -c lock_timeout=5000",
        }
        options["pool_timeout"] = 5
    engine = create_engine(database_url, **options)
    if database_url.get_backend_name() == "sqlite":
        # Every pooled SQLite connection must enforce the same ownership FKs as Postgres.
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def transaction(factory: sessionmaker[Session]) -> Iterator[Session]:
    """A fresh transaction per operation preserves earlier committed stages on failure."""
    with factory() as session, session.begin():
        yield session
