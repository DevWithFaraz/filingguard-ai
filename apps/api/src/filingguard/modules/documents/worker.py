"""No secrets, parser logs or raw exceptions leave this short-lived worker."""

import json
import logging
import os
import sys
import warnings


def main():
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    if os.name != "nt":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    from filingguard.integrations.storage.service import MAX_FILE_BYTES, PDFValidationError
    from filingguard.modules.documents.extraction import extract_pdf_in_worker

    try:
        data = sys.stdin.buffer.read(MAX_FILE_BYTES + 1)
        result = extract_pdf_in_worker(data)
        output = {"document": result.model_dump(mode="json")}
    except PDFValidationError as error:
        output = {"error": error.code}
    except Exception:
        output = {"error": "malformed_pdf"}
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
