"""Explicit read-only Neon check; never print the connection URL or DB errors."""

import json
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool


def main() -> int:
    location = Path(__file__).resolve().parents[1] / ".env"
    try:
        value = dotenv_values(location).get("DATABASE_URL")
        if not value:
            raise ValueError("missing_configuration")
        url = make_url(value)
        if url.drivername != "postgresql+psycopg":
            raise ValueError("unexpected_driver")
        if not url.host or not url.host.endswith(".neon.tech"):
            raise ValueError("expected_neon_host")
        if url.query.get("sslmode") not in ("require", "verify-ca", "verify-full"):
            raise ValueError("ssl_required")
        engine = create_engine(
            url, poolclass=NullPool,
            connect_args={"connect_timeout": 15, "application_name": "filingguard-access-check"},
        )
        try:
            with engine.connect() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                connection.execute(text("SET LOCAL statement_timeout = '10s'"))
                row = connection.execute(text(
                    "SELECT current_setting('server_version') AS version"
                )).one()
                # Verify our client transport, not a proxy's server-side connection.
                tls = bool(connection.connection.driver_connection.pgconn.ssl_in_use)
                if not tls:
                    raise ValueError("unencrypted_connection")
                print(json.dumps({
                    "connection": "passed", "postgres_version": row.version,
                    "tls": tls, "read_only": True,
                    "pooled_endpoint": "-pooler" in url.host,
                }))
        finally:
            engine.dispose()
    except (SQLAlchemyError, ValueError, TypeError) as error:
        safe_reasons = {
            "missing_configuration", "unexpected_driver", "expected_neon_host", "ssl_required",
            "unencrypted_connection",
        }
        reason = str(error) if type(error) is ValueError and str(error) in safe_reasons else None
        print(json.dumps({"connection": "failed", "error_kind": type(error).__name__,
                          "reason": reason}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
