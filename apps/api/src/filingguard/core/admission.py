"""Bounded single-process admission. Proxy forwarding headers are not trusted."""

import re
import secrets
import time
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import BoundedSemaphore, RLock

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from filingguard.core.config import Settings
from filingguard.db.repository import AnalysisNotFound


class Admission:
    def __init__(self):
        self.slot = BoundedSemaphore(1)
        self._lock = RLock()
        self._buckets = OrderedDict()

    def limit(self, key: str, *, count: int, window: int):
        with self._lock:
            now = time.monotonic()
            for old, (deadline, _) in list(self._buckets.items()):
                if deadline <= now:
                    del self._buckets[old]
            deadline, used = self._buckets.get(key, (now + window, 0))
            if used >= count or (key not in self._buckets and len(self._buckets) >= 1024):
                raise OverflowError("Request limit reached")
            self._buckets[key] = (deadline, used + 1)


def lifecycle(request: Request):
    settings: Settings = request.app.state.settings
    if not settings.intake_enabled or settings.private_storage_directory is None:
        raise RuntimeError("Intake disabled")
    return request.app.state.analysis_runtime.get_lifecycle()


def issue_session(request: Request):
    with request.app.state.admission._lock:
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(UTC) + timedelta(minutes=55)
        lifecycle(request).repository.issue_session(sha256(token.encode()).hexdigest(), expiry)
        return {"token": token, "expires_at": expiry.isoformat()}


def authenticate(request: Request):
    token = request.headers.get("authorization", "")
    if not re.fullmatch(r"Bearer [A-Za-z0-9_-]{43}", token):
        raise AnalysisNotFound("Authorization required")
    return lifecycle(request).repository.resolve_session(sha256(token[7:].encode()).hexdigest())


class IntakeGuard:
    def __init__(self, app, settings: Settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path, method = scope["path"], scope["method"]
        analyses = path == "/api/v1/analyses" or path.startswith("/api/v1/analyses/")
        identity_login = path == "/api/v1/identities/login"
        identity_protected = path.startswith("/api/v1/identities") and not identity_login
        session = (path == "/api/v1/sessions" or identity_login) and method == "POST"
        private = analyses or identity_protected
        if not (private or session) or method == "OPTIONS":
            return await self.app(scope, receive, send)
        from filingguard.api.errors import _response

        request = Request(scope)
        original_send = send

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"cache-control"
                ] + [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]
            await original_send(message)

        send = private_send

        async def reject(status, code, message):
            response = _response(request, status, code, message)
            if status == 429:
                response.headers["Retry-After"] = "60"
            await response(scope, receive, send)

        if not self.settings.intake_enabled or self.settings.private_storage_directory is None:
            return await reject(503, "intake_disabled", "Document intake is disabled")
        origin = request.headers.get("origin")
        if (origin is not None and origin not in self.settings.cors_origins) or (
            session and not origin
        ):
            return await reject(403, "forbidden_origin", "Request origin is not allowed")
        admission = request.app.state.admission
        try:
            if session:
                peer = scope.get("client") or ("unknown", 0)
                admission.limit("issue:" + sha256(peer[0].encode()).hexdigest(), count=5, window=60)
            else:
                owner, expiry = await run_in_threadpool(authenticate, request)
                scope.setdefault("state", {}).update(owner_hash=owner, session_expiry=expiry)
                admission.limit("read:" + owner, count=120, window=60)
                if method == "POST":
                    admission.limit("submit:" + owner, count=10, window=3600)
        except AnalysisNotFound:
            return await reject(401, "unauthorized", "Session authorization is required")
        except OverflowError:
            return await reject(429, "rate_limited", "Too many requests; try again later")
        except Exception:
            return await reject(503, "service_unavailable", "Service is temporarily unavailable")
        acquired = False
        if analyses and method == "POST" and not path.endswith("/run"):
            acquired = admission.slot.acquire(blocking=False)
            if not acquired:
                return await reject(409, "busy", "Another document is being prepared; try again")
        try:
            if method == "POST":
                import asyncio

                limit = 10 * 1024 * 1024 if path.endswith("/file") else 650000
                content_length = request.headers.get("content-length")
                if content_length is not None and (
                    not re.fullmatch(r"[0-9]{1,10}", content_length) or int(content_length) > limit
                ):
                    return await reject(413, "file_too_large", "Request exceeds the size limit")
                chunks, size = [], 0
                deadline = asyncio.get_running_loop().time() + 15
                while True:
                    try:
                        remaining = deadline - asyncio.get_running_loop().time()
                        if remaining <= 0:
                            raise TimeoutError()
                        message = await asyncio.wait_for(receive(), timeout=remaining)
                    except TimeoutError:
                        return await reject(408, "request_timeout", "Request body timed out")
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > limit:
                        return await reject(413, "file_too_large", "Request exceeds the size limit")
                    chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
                body = b"".join(chunks)
                consumed = False

                async def bounded_receive():
                    nonlocal consumed
                    if consumed:
                        return await receive()
                    consumed = True
                    return {"type": "http.request", "body": body, "more_body": False}

                return await self.app(scope, bounded_receive, send)
            return await self.app(scope, receive, send)
        finally:
            if acquired:
                admission.slot.release()
