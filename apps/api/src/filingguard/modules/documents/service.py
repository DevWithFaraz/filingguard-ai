import json
import os
import subprocess
import sys
from hashlib import sha256

from filingguard.integrations.storage.service import MAX_FILE_BYTES, PDFValidationError
from filingguard.modules.documents.schemas import ExtractedDocument

PDF_ERRORS = {
    "encrypted_pdf": "Encrypted PDFs are unsupported; paste text instead.",
    "no_text": "PDF has no extractable text; paste text instead.",
    "page_limit": "PDF must contain between 1 and 20 pages.",
    "text_limit": "PDF exceeds 100,000 extracted characters.",
    "segment_limit": "Document exceeds the paragraph limit.",
    "parser_limit": "PDF exceeds parsing resource limits; paste text instead.",
    "malformed_pdf": "PDF cannot be parsed safely; paste text instead.",
}


def extract_pdf(data: bytes, *, timeout: float = 15) -> ExtractedDocument:
    if len(data) > MAX_FILE_BYTES:
        raise PDFValidationError("file_too_large", "PDF exceeds the 10 MiB limit.")
    if not data.startswith(b"%PDF-"):
        raise PDFValidationError("invalid_signature", "File must have a PDF signature.")
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
    }
    job = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "filingguard.modules.documents.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except OSError:
        raise PDFValidationError(
            "parser_unavailable", "PDF parser unavailable; paste text instead."
        ) from None
    try:
        if os.name == "nt":
            from filingguard.modules.documents.windows_job import WindowsJob

            job = WindowsJob(int(process._handle))
        output, _ = process.communicate(data, timeout=timeout)
        if process.returncode != 0 or len(output) > 1500000:
            raise PDFValidationError("parser_limit", PDF_ERRORS["parser_limit"])
        result = json.loads(output)
        if "error" in result:
            code = result["error"] if result["error"] in PDF_ERRORS else "malformed_pdf"
            raise PDFValidationError(code, PDF_ERRORS[code])
        document = ExtractedDocument.model_validate(result["document"])
        if (
            document.input_sha256 != sha256(data).hexdigest()
            or document.method != "pypdf-bounded-v1"
            or not document.pages
        ):
            raise ValueError("Worker result identity mismatch")
        return document
    except subprocess.TimeoutExpired:
        raise PDFValidationError(
            "parser_timeout", "PDF parsing timed out; paste text instead."
        ) from None
    except PDFValidationError:
        raise
    except Exception:
        raise PDFValidationError(
            "parser_unavailable", "PDF parser unavailable; paste text instead."
        ) from None
    finally:
        if job is not None:
            job.close()
        if process.poll() is None:
            process.kill()
        process.communicate()
