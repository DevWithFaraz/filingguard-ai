"""Importable synthetic runners without test-client or pytest startup side effects."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

from filingguard.integrations.providers.transport import BoundedProviderClient
from filingguard.modules.analyses.execution import StageResult
from filingguard.modules.analyses.schemas import Coverage, StageStatus


def completed(_analysis, _budget):
    return StageResult(status=StageStatus.COMPLETED, coverage=Coverage(eligible=1, evaluated=1))


def forged_citation(analysis, _budget):
    from uuid import uuid4

    from filingguard.db.models import Citation

    return StageResult(
        status=StageStatus.PARTIAL, reason="Synthetic extracted occurrence",
        coverage=Coverage(eligible=1, unavailable=1),
        records=(Citation(
            id=uuid4(), analysis_id=analysis.id, raw_text="1 U.S. 1",
            normalized_text=None, segment_id=analysis.review_segments[0].id,
            start_offset=0, end_offset=8, page_number=None,
            verification_status="not_run", authority_id=None,
            extraction_metadata={"parser_version": "synthetic", "kind": "full_case",
                                 "support": "recognized"},
        ),),
    )


def held(analysis, budget):
    paths = json.loads(analysis.document_snapshot["text"])
    Path(paths["entered"]).touch()
    while not Path(paths["release"]).exists():
        budget.remaining()
        time.sleep(0.02)
    return completed(analysis, budget)


def fail(_analysis, _budget):
    raise RuntimeError("SYNTHETIC_PRIVATE_SENTINEL")


def spend_budget(analysis, budget):
    budget.reserve()
    budget.reserve()
    return completed(analysis, budget)


def stuck_provider(analysis, budget):
    text = analysis.document_snapshot["text"]
    path = Path(json.loads(text)["marker"] if text.startswith("{") else text)

    def fake_response(_request):
        path.write_text(str(os.getpid()))
        while True:
            time.sleep(0.02)

    with BoundedProviderClient(
        "groq", "SYNTHETIC_KEY", budget, transport=httpx.MockTransport(fake_response)
    ) as client:
        client.request_json("POST", "/openai/v1/chat/completions", payload={"test": True})
    return completed(analysis, budget)


def stuck_descendant(analysis, budget):
    path = analysis.document_snapshot["text"]
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time,sys;from pathlib import Path;"
            "p=Path(sys.argv[1]);\nwhile True:\n p.write_text(str(time.time_ns()));time.sleep(.03)",
            path,
        ],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    child.wait()
    return completed(analysis, budget)
