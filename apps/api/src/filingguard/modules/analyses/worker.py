"""Run trusted server-registered stage code; never accept a client-selected callable."""

import importlib
import json
import logging
import math
import os
import sys
import time
import warnings
from contextlib import redirect_stderr, redirect_stdout


def main():
    output = sys.stdout.buffer
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    with open(os.devnull, "w") as quiet, redirect_stdout(quiet), redirect_stderr(quiet):
        from filingguard.db.models import Analysis
        from filingguard.integrations.providers.runtime import ProviderBudget, ProviderUnavailable
        from filingguard.modules.analyses.execution import (
            ANALYSIS_FIELDS,
            CONTEXT_TYPES,
            MAX_INPUT_BYTES,
            MAX_OUTPUT_BYTES,
            ReviewSegment,
            result_to_wire,
            row_from_wire,
            validate_segments,
        )
        from filingguard.modules.analyses.schemas import StageName

        budget = None
        try:
            request = json.loads(sys.stdin.buffer.read(MAX_INPUT_BYTES + 1))
            remaining = request["deadline"] - time.monotonic()
            if os.name != "nt":
                import resource

                resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024,) * 2)
                cpu = max(1, math.ceil(remaining))
                resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if remaining <= 0:
                raise TimeoutError()
            budget = ProviderBudget(
                deadline=request["deadline"], max_attempts=request["attempts_left"]
            )
            if request["analysis"].keys() - set(ANALYSIS_FIELDS):
                raise ValueError("Unexpected snapshot fields")
            analysis = row_from_wire(Analysis, request["analysis"])
            segments = request.get("segments", [])
            if not isinstance(segments, list) or len(segments) > 2000:
                raise ValueError("Invalid review segment context")
            analysis.review_segments = tuple(ReviewSegment.model_validate(s) for s in segments)
            if analysis.review_segments:
                validate_segments(analysis, analysis.review_segments)
            context = request.get("context", {})
            if not isinstance(context, dict) or context.keys() - CONTEXT_TYPES.keys():
                raise ValueError("Unexpected prior context")
            for key, model in CONTEXT_TYPES.items():
                rows = context.get(key, [])
                if not isinstance(rows, list) or len(rows) > 200:
                    raise ValueError("Prior context exceeds bounds")
                decoded = tuple(row_from_wire(model, row) for row in rows)
                if any(row.analysis_id != analysis.id for row in decoded):
                    raise ValueError("Prior context owner mismatch")
                setattr(analysis, "review_" + key, decoded)
            credentials = request.get("credentials", {})
            if (not isinstance(credentials, dict)
                or credentials.keys() - {"courtlistener", "groq", "groq_model"}
                or any(not isinstance(v, str) or len(v) > 4096 for v in credentials.values())):
                raise ValueError("Invalid provider credential boundary")
            analysis.provider_credentials = credentials
            module, name = request["runner"].split(":")
            runner = getattr(importlib.import_module(module), name)
            result = runner(analysis, budget)
            result.validate(StageName(request["stage"]))
            envelope = {"result": result_to_wire(result), "attempts_used": budget.attempts_used}
        except ProviderUnavailable:
            envelope = {"error": "provider", "attempts_used": budget.attempts_used if budget else 0}
        except TimeoutError:
            envelope = {"error": "deadline", "attempts_used": budget.attempts_used if budget else 0}
        except Exception:
            envelope = {"error": "failed", "attempts_used": budget.attempts_used if budget else 0}
        data = json.dumps(envelope, ensure_ascii=False, allow_nan=False).encode()
        if len(data) > MAX_OUTPUT_BYTES:
            data = json.dumps({"error": "limit", "attempts_used": budget.attempts_used}).encode()
        output.write(data)
        output.flush()


if __name__ == "__main__":
    main()
