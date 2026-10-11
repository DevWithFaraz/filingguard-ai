"""Disposable localhost preparation preview. Never migrates the configured Neon DB."""

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from filingguard.db.models import EvidenceRecord
from filingguard.db.session import create_db_engine


def save_model_receipt():
    """Explicit synthetic preview only: numeric diagnostics, no original text/URLs."""
    engine = create_db_engine()
    rows = []
    try:
        with Session(engine) as session:
            for evidence in session.scalars(
                select(EvidenceRecord).where(
                    EvidenceRecord.source_type == "document",
                )
            ):
                metadata = evidence.source_metadata or {}
                if "proposition_status" not in metadata:
                    continue
                rows.append(
                    {
                        key: metadata.get(key)
                        for key in (
                            "proposition_status",
                            "prompt_tokens",
                            "completion_tokens",
                            "elapsed_seconds",
                            "token_quota",
                            "batch_size",
                            "request_group",
                        )
                    }
                    | {
                        "selected_characters": sum(
                            p["end"] - p["start"] for p in metadata.get("selected_passages", [])
                        )
                    }
                )
        target = Path(__file__).resolve().parents[3] / ".runtime/live-preview-token-receipt.json"
        if not rows:
            return  # Keep the last evidence receipt after the test resets/deletes its demo.
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps({"checked_at": datetime.now(UTC).isoformat(), "checks": rows}, indent=2)
            + "\n",
            encoding="utf-8",
        )
    finally:
        engine.dispose()


def collect_model_receipts(stop):
    while not stop.wait(2):
        try:
            save_model_receipt()
        except Exception:
            pass  # This diagnostic cannot block synthetic preview execution.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-semantic",
        action="store_true",
        help="Opt into genuine model review of the synthetic demo; free credits only",
    )
    parser.add_argument("--port", type=int, choices=(8001, 8002), default=8001)
    args = parser.parse_args()
    api_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="filingguard-synthetic-preview-") as temporary:
        root = Path(temporary)
        os.environ.update(
            DATABASE_URL="sqlite+pysqlite:///" + (root / "preview.sqlite").as_posix(),
            PRIVATE_STORAGE_DIRECTORY=str(root / "private"),
            INTAKE_ENABLED="true",
            SOURCE_VERIFICATION_ENABLED="false",
            SEMANTIC_REVIEW_ENABLED="true" if args.live_semantic else "false",
            REVIEW_STAGE_TIMEOUT_SECONDS="60" if args.live_semantic else "30",
            MAX_PROVIDER_ATTEMPTS="5",
            CORS_ORIGINS='["http://127.0.0.1:5174","http://localhost:5174",'
            '"http://127.0.0.1:5175","http://localhost:5175"]',
        )
        engine = create_db_engine()
        config = Config(str(api_root / "alembic.ini"))
        config.set_main_option("script_location", str(api_root / "migrations"))
        try:
            with engine.begin() as connection:
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        finally:
            engine.dispose()
        stop_receipts = Event()
        if args.live_semantic:
            Thread(target=collect_model_receipts, args=(stop_receipts,), daemon=True).start()
        print(f"Synthetic/public-data-only preview: http://127.0.0.1:{args.port}")
        try:
            uvicorn.run(
                "filingguard.main:create_app",
                factory=True,
                host="127.0.0.1",
                port=args.port,
                workers=1,
                access_log=False,
            )
        finally:
            stop_receipts.set()
            if args.live_semantic:
                save_model_receipt()


if __name__ == "__main__":
    main()
