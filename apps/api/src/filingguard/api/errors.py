"""Public errors never echo filing text, provider payloads or configuration values."""

import logging
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from filingguard.api.contracts import ApiError, ApiErrorDetail

logger = logging.getLogger(__name__)
PUBLIC_HTTP_ERRORS = {
    400: ("bad_request", "Request could not be accepted"),
    401: ("unauthorized", "Session authorization is required"),
    403: ("forbidden", "Request is not allowed"),
    404: ("not_found", "Requested resource was not found"),
    405: ("method_not_allowed", "Request method is not allowed"),
    409: ("conflict", "Request conflicts with current state"),
    413: ("file_too_large", "Request exceeds the size limit"),
    415: ("unsupported_media_type", "Supply a PDF with application/pdf content type"),
    429: ("rate_limited", "Too many requests; try again later"),
    503: ("service_unavailable", "Service is temporarily unavailable"),
}

SAFE_DOCUMENT_ERRORS = {
    "encrypted_pdf": (422, "Encrypted PDFs are unsupported; paste text instead."),
    "no_text": (422, "PDF has no extractable text; paste text instead."),
    "page_limit": (422, "PDF must contain between 1 and 20 pages."),
    "text_limit": (422, "Document exceeds 100,000 characters."),
    "segment_limit": (422, "Document exceeds the paragraph limit."),
    "parser_limit": (422, "PDF exceeds parsing resource limits; paste text instead."),
    "malformed_pdf": (422, "PDF cannot be parsed safely; paste text instead."),
    "parser_timeout": (422, "PDF parsing timed out; paste text instead."),
    "parser_unavailable": (503, "PDF parser unavailable; paste text instead."),
    "invalid_signature": (422, "File must have a PDF signature."),
    "invalid_text": (422, "Supply nonempty text up to 100,000 characters."),
    "file_too_large": (413, "PDF exceeds the 10 MiB limit."),
}


class DocumentError(HTTPException):
    def __init__(self, code: str):
        self.code = code if code in SAFE_DOCUMENT_ERRORS else "malformed_pdf"
        status, _ = SAFE_DOCUMENT_ERRORS[self.code]
        super().__init__(status)


def _response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", uuid4())
    body = ApiError(error=ApiErrorDetail(code=code, message=message, request_id=request_id))
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json"),
        headers={
            "Cache-Control": "no-store",
            "X-Request-ID": str(request_id),
        },
    )


def install_error_boundary(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_boundary(request: Request, call_next):
        request.state.request_id = uuid4()
        try:
            response = await call_next(request)
        except Exception as error:
            # Exception messages/tracebacks can contain provider text or private inputs.
            correlation_id = None
            header_cid = request.headers.get("x-correlation-id")
            if header_cid:
                try:
                    correlation_id = str(UUID(header_cid))
                except (ValueError, AttributeError):
                    pass
            if not correlation_id:
                query_aid = request.query_params.get("analysis_id")
                if query_aid:
                    try:
                        correlation_id = str(UUID(query_aid))
                    except (ValueError, AttributeError):
                        pass
            if not correlation_id:
                for part in request.url.path.strip("/").split("/"):
                    try:
                        correlation_id = str(UUID(part))
                        break
                    except (ValueError, AttributeError):
                        continue
            if correlation_id:
                logger.error(
                    "API failure (%s), request_id=%s correlation_id=%s",
                    type(error).__name__,
                    request.state.request_id,
                    correlation_id,
                )
            else:
                logger.error(
                    "API failure (%s), request_id=%s",
                    type(error).__name__,
                    request.state.request_id,
                )
            return _response(request, 500, "internal_error", "Request could not be completed")
        response.headers["X-Request-ID"] = str(request.state.request_id)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return _response(request, 422, "validation_error", "Request fields are invalid")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        if isinstance(error, DocumentError):
            status, message = SAFE_DOCUMENT_ERRORS[error.code]
            return _response(request, status, error.code, message)
        code, message = PUBLIC_HTTP_ERRORS.get(error.status_code, ("http_error", "Request failed"))
        response = _response(request, error.status_code, code, message)
        retry_after = (error.headers or {}).get("Retry-After", "")
        if retry_after.isdigit() and len(retry_after) <= 6:
            response.headers["Retry-After"] = retry_after
        allowed = (error.headers or {}).get("Allow", "")
        methods = [method.strip() for method in allowed.split(",")]
        if allowed and all(
            method in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
            for method in methods
        ):
            response.headers["Allow"] = ", ".join(methods)
        return response
