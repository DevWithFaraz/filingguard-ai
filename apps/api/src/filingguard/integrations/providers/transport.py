"""Fixed-host HTTP boundary with cooperative deadlines and bounded retries.

The stage supervisor must terminate blocking work at the hard review deadline.
No provider-specific verdicts, environment loading, or SDK retries live here.
"""

import json
import logging
import math
import re
import time
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from threading import BoundedSemaphore, Lock
from typing import Literal

import httpx

from .runtime import ProviderBudget, ProviderDeadline, ProviderUnavailable

_BASES = {
    "courtlistener": ("https://www.courtlistener.com", "/api/rest/v4/", "Token"),
    "groq": ("https://api.groq.com", "/openai/v1/", "Bearer"),
}
_RETRY_STATUSES = {429, 502, 503, 504}
_QUIET = ContextVar("provider_transport_quiet", default=False)
_LOG_LOCK = Lock()


class _ProviderLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _QUIET.get()


_LOG_FILTER = _ProviderLogFilter()


def _install_log_filter() -> None:
    # HTTPX logs request URLs; HTTPcore debug records can contain headers.
    with _LOG_LOCK:
        names = {
            "httpx",
            "httpcore",
            "httpcore.connection",
            "httpcore.http11",
            "httpcore.http2",
            "httpcore.proxy",
            "httpcore.socks",
        }
        names.update(
            name
            for name in logging.Logger.manager.loggerDict
            if name.startswith(("httpx.", "httpcore."))
        )
        for name in names:
            logging.getLogger(name).addFilter(_LOG_FILTER)


@dataclass(frozen=True)
class ProviderPolicy:
    max_request_bytes: int = 128 * 1024
    max_response_bytes: int = 4 * 1024 * 1024
    call_timeout: float = 20.0
    max_concurrency: int = 2
    courtlistener_retries: int = 1
    groq_retries: int = 0
    retry_base: float = 0.25
    retry_cap: float = 2.0

    def __post_init__(self) -> None:
        integers = (
            (self.max_request_bytes, 128 * 1024),
            (self.max_response_bytes, 4 * 1024 * 1024),
            (self.max_concurrency, 2),
        )
        numbers = ((self.call_timeout, 20), (self.retry_base, 2), (self.retry_cap, 2))
        if (
            any(type(value) is not int or not 1 <= value <= cap for value, cap in integers)
            or any(
                type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= cap
                for value, cap in numbers
            )
            or self.retry_base > self.retry_cap
            or type(self.courtlistener_retries) is not int
            or self.courtlistener_retries not in (0, 1)
            or type(self.groq_retries) is not int
            or self.groq_retries != 0
        ):
            raise ProviderUnavailable("invalid_policy")


_DEFAULT_POLICY = ProviderPolicy()


class BoundedProviderClient:
    def __init__(
        self,
        provider: Literal["courtlistener", "groq"],
        credential: str,
        budget: ProviderBudget,
        policy: ProviderPolicy = _DEFAULT_POLICY,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not isinstance(budget, ProviderBudget) or not isinstance(policy, ProviderPolicy):
            raise ProviderUnavailable("invalid_policy")
        if (
            not isinstance(provider, str)
            or provider not in _BASES
            or not isinstance(credential, str)
            or not 1 <= len(credential) <= 4096
            or any(ord(char) < 33 or ord(char) > 126 for char in credential)
        ):
            raise ProviderUnavailable("invalid_request")
        self.provider = provider
        self.last_token_quota: dict[str, int | float] = {}
        self._quota_observed_at = 0.0
        self.budget = budget
        self.policy = policy
        self._base, self._prefix, scheme = _BASES[provider]
        self._headers = {
            "Authorization": f"{scheme} {credential}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._slots = budget._slots
        self._local_slot = BoundedSemaphore(1) if policy.max_concurrency == 1 else None
        _install_log_filter()
        self._client = httpx.Client(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(
                max_connections=policy.max_concurrency,
                max_keepalive_connections=policy.max_concurrency,
            ),
        )

    def __enter__(self) -> "BoundedProviderClient":
        if self._client.is_closed:
            raise ProviderUnavailable("client_closed")
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        token = _QUIET.set(True)
        try:
            self._client.close()
        finally:
            _QUIET.reset(token)

    def _remaining(self, deadline: float) -> float:
        remaining = self.budget.remaining()
        call_remaining = deadline - time.monotonic()
        if call_remaining <= 0:
            raise ProviderUnavailable("timeout")
        return min(remaining, call_remaining)

    def _encode_request(
        self,
        method: str,
        path: str,
        payload: dict | None,
        params: Mapping[str, str | int | float | bool] | None,
        deadline: float,
    ) -> tuple[httpx.URL, bytes]:
        if (
            method not in ("GET", "POST")
            or not isinstance(path, str)
            or not path.startswith(self._prefix)
            or not re.fullmatch(r"/[A-Za-z0-9_./~-]+", path)
            or "//" in path
            or any(part in (".", "..") for part in path.split("/"))
            or (payload is not None and (not isinstance(payload, dict) or method != "POST"))
        ):
            raise ProviderUnavailable("invalid_request")
        if len(path) > self.policy.max_request_bytes:
            raise ProviderUnavailable("request_too_large")
        if params is not None:
            if not isinstance(params, Mapping) or any(
                not isinstance(key, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key)
                or type(value) not in (str, int, float, bool)
                or (type(value) is float and not math.isfinite(value))
                for key, value in params.items()
            ):
                raise ProviderUnavailable("invalid_request")
            if sum(len(key) + len(str(value)) for key, value in params.items()) > (
                self.policy.max_request_bytes
            ):
                raise ProviderUnavailable("request_too_large")
        url = httpx.URL(self._base + path, params=params)
        content = bytearray()
        if payload is not None:
            for piece in json.JSONEncoder(
                ensure_ascii=True, allow_nan=False, separators=(",", ":")
            ).iterencode(payload):
                self._remaining(deadline)
                content.extend(piece.encode("ascii"))
                if len(content) > self.policy.max_request_bytes:
                    raise ProviderUnavailable("request_too_large")
        if len(url.raw_path) + len(content) > self.policy.max_request_bytes:
            raise ProviderUnavailable("request_too_large")
        self._remaining(deadline)
        return url, bytes(content)

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        *,
        params: Mapping[str, str | int | float | bool] | None = None,
        token_cost: int | None = None,
    ) -> object:
        deadline = time.monotonic() + self.policy.call_timeout
        token = _QUIET.set(True)
        acquired = False
        local_acquired = False
        error: ProviderUnavailable | None = None
        try:
            url, content = self._encode_request(method, path, payload, params, deadline)
            if token_cost is not None:
                # Admission waits belong to the finite stage queue. Once admitted,
                # HTTP encoding/transport/retries retain their 20-second operation cap.
                self._pace_tokens(token_cost, self.budget.deadline)
                deadline = min(self.budget.deadline, time.monotonic() + self.policy.call_timeout)
            acquired = self._slots.acquire(timeout=self._remaining(deadline))
            self._remaining(deadline)
            if not acquired:
                raise ProviderUnavailable("timeout")
            if self._local_slot is not None:
                local_acquired = self._local_slot.acquire(timeout=self._remaining(deadline))
                self._remaining(deadline)
                if not local_acquired:
                    raise ProviderUnavailable("timeout")
            if self._client.is_closed:
                raise ProviderUnavailable("client_closed")
            return self._request(method, url, content, deadline)
        except ProviderUnavailable as exc:
            error = (
                ProviderDeadline()
                if isinstance(exc, ProviderDeadline)
                else ProviderUnavailable(exc.code)
            )
        except (TypeError, ValueError, OverflowError, RecursionError):
            error = ProviderUnavailable("invalid_request")
        except httpx.HTTPError:
            error = ProviderUnavailable("network_failure")
        finally:
            if local_acquired:
                self._local_slot.release()
            if acquired:
                self._slots.release()
            _QUIET.reset(token)
        # Raise outside the handler so a raw provider exception is not retained as context.
        raise error from None

    def _pace_tokens(self, cost: int, deadline: float) -> None:
        """Advisory pacing of a new call, never a retry or an exact tokenizer claim."""
        if self.provider != "groq" or type(cost) is not int or not 1 <= cost <= 100000:
            raise ProviderUnavailable("invalid_request")
        limit = self.last_token_quota.get("limit")
        remaining = self.last_token_quota.get("remaining")
        if not isinstance(limit, int) or not isinstance(remaining, int) or limit <= 0:
            return
        if cost > limit:
            raise ProviderUnavailable("rate_limited")
        refill = limit / 60
        available = min(
            limit, remaining + max(0, time.monotonic() - self._quota_observed_at) * refill
        )
        wait = max(0, (cost - available) / refill)
        if wait:
            wait += 0.25
            # Leave time for the HTTP call; do not shorten a required quota wait.
            if wait + 1 >= self._remaining(deadline):
                raise ProviderUnavailable("rate_limited")
            time.sleep(wait)
            self._remaining(deadline)

    def _retry_wait(self, header: str | None, retry: int, deadline: float) -> None:
        wait = min(self.policy.retry_cap, self.policy.retry_base * 2**retry)
        if header is not None:
            try:
                if re.fullmatch(r"[0-9]+", header.strip()):
                    wait = float(header.strip())
                else:
                    date = parsedate_to_datetime(header)
                    if date.tzinfo is None:
                        date = date.replace(tzinfo=UTC)
                    wait = max(0.0, (date - datetime.now(UTC)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
        if not math.isfinite(wait) or wait >= self._remaining(deadline):
            raise ProviderUnavailable("rate_limited")
        if wait:
            time.sleep(wait)
        self._remaining(deadline)

    def _request(self, method: str, url: httpx.URL, content: bytes, deadline: float) -> object:
        retries = self.policy.courtlistener_retries if self.provider == "courtlistener" else 0
        for attempt in range(retries + 1):
            timeout = self._remaining(deadline)
            self.budget.reserve()
            retry_after = None
            failure = "network_failure"
            retryable = False
            try:
                # Explicit Request avoids client cookies or other state entering future attempts.
                request = httpx.Request(
                    method,
                    url,
                    headers=self._headers,
                    content=content,
                    extensions={"timeout": httpx.Timeout(timeout).as_dict()},
                )
                response = self._client.send(request, stream=True)
                try:
                    self.last_token_quota = {}
                    self._quota_observed_at = time.monotonic()
                    if self.provider == "groq":
                        for name in ("limit", "remaining"):
                            value = response.headers.get(f"x-ratelimit-{name}-tokens", "")
                            if re.fullmatch(r"[0-9]{1,9}", value):
                                self.last_token_quota[name] = int(value)
                        reset = response.headers.get("x-ratelimit-reset-tokens", "")
                        duration = re.fullmatch(r"(?:(\d{1,3})m)?(\d{1,3}(?:\.\d{1,3})?)s", reset)
                        if duration:
                            self.last_token_quota["reset_seconds"] = min(
                                86400, int(duration[1] or 0) * 60 + float(duration[2])
                            )
                    self._remaining(deadline)
                    status = response.status_code
                    if not 200 <= status < 300:
                        failure = "rate_limited" if status == 429 else "http_failure"
                        retryable = status in _RETRY_STATUSES
                        retry_after = response.headers.get("Retry-After")
                    else:
                        length = response.headers.get("Content-Length")
                        if length is not None:
                            if not re.fullmatch(r"[0-9]+", length):
                                raise ProviderUnavailable("invalid_response")
                            if int(length) > self.policy.max_response_bytes:
                                raise ProviderUnavailable("response_too_large")
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            self._remaining(deadline)
                            if len(body) + len(chunk) > self.policy.max_response_bytes:
                                raise ProviderUnavailable("response_too_large")
                            body.extend(chunk)
                        self._remaining(deadline)
                        result = json.loads(body)
                        self._remaining(deadline)
                        return result
                finally:
                    response.close()
                    self._remaining(deadline)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                failure = (
                    "timeout" if isinstance(exc, httpx.TimeoutException) else "network_failure"
                )
                retryable = isinstance(exc, (httpx.TimeoutException, httpx.ConnectError))
            except (httpx.HTTPError, ValueError, UnicodeError, RecursionError):
                failure = "invalid_response"
            self._remaining(deadline)
            if not retryable or attempt == retries:
                raise ProviderUnavailable(failure)
            self._retry_wait(retry_after, attempt, deadline)
        raise ProviderUnavailable()
