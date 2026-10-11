import gzip
import logging
import math
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from filingguard.integrations.providers import (
    BoundedProviderClient,
    ProviderBudget,
    ProviderDeadline,
    ProviderPolicy,
    ProviderUnavailable,
    runtime,
    transport,
)

PATH = "/api/rest/v4/citation-lookup/"
GROQ_PATH = "/openai/v1/chat/completions"
SECRET = "synthetic-secret"
RAW = "synthetic-private-payload"


def test_groq_quota_receipt_allowlists_only_bounded_token_numbers():
    responses = iter(
        [
            httpx.Response(
                200,
                json={},
                headers={
                    "x-ratelimit-limit-tokens": "8000",
                    "x-ratelimit-remaining-tokens": "1234",
                    "x-ratelimit-reset-tokens": "1m2.5s",
                    "Authorization": SECRET,
                    "x-ratelimit-remaining-requests": "999",
                },
            ),
            httpx.Response(
                429,
                headers={
                    "x-ratelimit-limit-tokens": RAW,
                    "x-ratelimit-remaining-tokens": "-1",
                    "x-ratelimit-reset-tokens": "nan",
                },
            ),
        ]
    )
    with client(lambda _: next(responses), provider="groq") as provider:
        provider.request_json("POST", GROQ_PATH, {})
        assert provider.last_token_quota == {
            "limit": 8000,
            "remaining": 1234,
            "reset_seconds": 62.5,
        }
        assert_code("rate_limited", lambda: provider.request_json("POST", GROQ_PATH, {}))
        assert provider.last_token_quota == {}


def test_quota_pacing_waits_before_new_call_without_retry(clock):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={},
            headers={
                "x-ratelimit-limit-tokens": "8000",
                "x-ratelimit-remaining-tokens": "1000",
            },
        )

    with client(handler, provider="groq") as provider:
        provider.request_json("POST", GROQ_PATH, {}, token_cost=2000)
        provider.request_json("POST", GROQ_PATH, {}, token_cost=2000)
        assert clock.sleeps == pytest.approx([7.75])
        assert len(calls) == provider.budget.attempts_used == 2
        # Admission can wait longer than one HTTP operation, within the stage cap.
        provider.request_json("POST", GROQ_PATH, {}, token_cost=7000)
        assert clock.sleeps == pytest.approx([7.75, 45.25])
        # A wait exceeding the stage deadline is rejected before another attempt.
        assert_code(
            "rate_limited", lambda: provider.request_json("POST", GROQ_PATH, {}, token_cost=7000)
        )
        assert len(calls) == provider.budget.attempts_used == 3


def test_quota_pacing_does_not_retry_a_provider_429(clock):
    with client(lambda _: httpx.Response(429), provider="groq") as provider:
        assert_code(
            "rate_limited", lambda: provider.request_json("POST", GROQ_PATH, {}, token_cost=2000)
        )
        assert provider.budget.attempts_used == 1
        assert not clock.sleeps


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(runtime.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(transport.time, "sleep", clock.sleep)
    return clock


def budget(**kwargs):
    return ProviderBudget(time.monotonic() + 90, **kwargs)


def client(handler, *, provider="courtlistener", shared=None, policy=None):
    return BoundedProviderClient(
        provider,
        SECRET,
        shared or budget(),
        policy or ProviderPolicy(),
        httpx.MockTransport(handler),
    )


def assert_code(expected, action):
    with pytest.raises(ProviderUnavailable) as caught:
        action()
    assert caught.value.code == expected
    assert str(caught.value) == expected
    return caught.value


def test_budget_defaults_deadline_and_shared_accounting(clock):
    shared = ProviderBudget(101)
    assert shared.remaining() == 1
    assert shared.max_attempts == 60
    shared.reserve()
    assert shared.attempts_used == 1
    clock.now = 101
    with pytest.raises(ProviderDeadline) as caught:
        shared.reserve()
    assert caught.value.code == "deadline_exceeded"
    assert shared.attempts_used == 1
    assert_code("deadline_exceeded", shared.remaining)


def test_reservation_is_atomic():
    shared = budget(max_attempts=7, attempts_used=2)

    def reserve(_):
        try:
            shared.reserve()
            return True
        except ProviderUnavailable as exc:
            assert exc.code == "request_budget_exhausted"
            return False

    with ThreadPoolExecutor(max_workers=16) as pool:
        assert sum(pool.map(reserve, range(40))) == 5
    assert shared.attempts_used == 7


def test_budget_across_clients():
    shared = budget(max_attempts=2)
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with client(handler, shared=shared) as first, client(handler, shared=shared) as second:
        assert first.request_json("GET", PATH) == {"ok": True}
        second.request_json("GET", PATH)
        assert_code("request_budget_exhausted", lambda: first.request_json("GET", PATH))
    assert len(seen) == shared.attempts_used == 2


@pytest.mark.parametrize(
    "provider,path,scheme,host",
    [
        ("courtlistener", PATH, "Token", "www.courtlistener.com"),
        ("groq", GROQ_PATH, "Bearer", "api.groq.com"),
    ],
)
def test_credentials_headers_only_and_structured_params(provider, path, scheme, host, caplog):
    seen = []

    def handler(request):
        seen.append(request)
        logging.getLogger("httpcore.http11").debug("headers %s", request.headers)
        return httpx.Response(200, json=[1, {"ok": True}])

    with caplog.at_level(logging.DEBUG), client(handler, provider=provider) as service:
        assert service.request_json(
            "POST",
            path,
            {"excerpt": RAW},
            params={
                "page": 2,
                "q": "https://untrusted.invalid/?x=#fragment",
                "active": True,
            },
        ) == [1, {"ok": True}]
    request = seen[0]
    assert request.url.host == host
    assert request.url.scheme == "https"
    assert request.headers["authorization"] == f"{scheme} {SECRET}"
    assert SECRET not in str(request.url)
    assert SECRET.encode() not in request.content
    assert RAW.encode() in request.content
    assert not caplog.records


@pytest.mark.parametrize(
    "path",
    [
        "https://untrusted.invalid/api/rest/v4/",
        "//untrusted.invalid/api/rest/v4/",
        "/api/rest/v4/../opinions/",
        "/api/rest/v4/./opinions/",
        "/api/rest/v4/a/../../",
        "/api/rest/v4/%2e%2e/",
        "/api/rest/v4/%252e%252e/",
        "/api/rest/v4/%2f%2fhost/",
        "/api/rest/v4/a\\b",
        "/api/rest/v4/?q=secret",
        "/api/rest/v4/#fragment",
        "/api/rest/v4//host/",
        "/api/rest/v40/",
        "/openai/v1/chat/completions",
        "api/rest/v4/",
        "/api/rest/v4/\n",
        "/api/rest/v4/é/",
    ],
)
def test_reject_unsafe_paths(path):
    shared = budget()
    with client(lambda _: pytest.fail("HTTP must not run"), shared=shared) as service:
        assert_code("invalid_request", lambda: service.request_json("GET", path))
    assert shared.attempts_used == 0


@pytest.mark.parametrize(
    "method,payload,params",
    [
        ("DELETE", None, None),
        ("get", None, None),
        ("GET", {}, None),
        ("POST", [], None),
        ("GET", None, "q=secret"),
        ("GET", None, {"x": []}),
        ("GET", None, {"x": None}),
        ("GET", None, {"x": math.nan}),
        ("GET", None, {"bad&key": "x"}),
        ("GET", None, {1: "x"}),
        ("POST", {"secret": object()}, None),
        ("POST", {"value": math.inf}, None),
    ],
)
def test_reject_invalid_request(method, payload, params):
    with client(lambda _: pytest.fail("HTTP must not run")) as service:
        assert_code(
            "invalid_request",
            lambda: service.request_json(
                method,
                PATH,
                payload,
                params=params,
            ),
        )


@pytest.mark.parametrize("provider,path", [("groq", PATH), ("courtlistener", GROQ_PATH)])
def test_provider_prefix_cannot_cross(provider, path):
    with client(lambda _: pytest.fail("HTTP must not run"), provider=provider) as service:
        assert_code("invalid_request", lambda: service.request_json("GET", path))


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 500, 501, 301, 302, 307, 308])
def test_non_retryable_http_failures(status, clock):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status, headers={"Location": "https://untrusted.invalid"}, text=RAW)

    with client(handler) as service:
        exc = assert_code("http_failure", lambda: service.request_json("GET", PATH))
    assert len(seen) == 1
    assert clock.sleeps == []
    assert RAW not in repr(exc)


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_courtlistener_one_retry(status, clock):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status if len(seen) == 1 else 200, json={"ok": True})

    shared = budget()
    with client(handler, shared=shared) as service:
        assert service.request_json("GET", PATH) == {"ok": True}
    assert shared.attempts_used == len(seen) == 2
    assert clock.sleeps == [0.25]


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_groq_never_retries(status, clock):
    shared = budget()
    with client(lambda _: httpx.Response(status), provider="groq", shared=shared) as service:
        assert_code(
            "rate_limited" if status == 429 else "http_failure",
            lambda: service.request_json("POST", GROQ_PATH, {}),
        )
    assert shared.attempts_used == 1
    assert clock.sleeps == []


def test_retry_exhaustion_and_request_quota(clock):
    with client(lambda _: httpx.Response(503)) as service:
        assert_code("http_failure", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 2
    shared = budget(max_attempts=1)
    with client(lambda _: httpx.Response(429), shared=shared) as service:
        assert_code("request_budget_exhausted", lambda: service.request_json("GET", PATH))
    assert shared.attempts_used == 1


@pytest.mark.parametrize(
    "error_type",
    [
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
    ],
)
@pytest.mark.parametrize("provider", ["courtlistener", "groq"])
def test_network_retry_policy_and_sanitization(error_type, provider, clock, caplog):
    shared = budget()

    def handler(request):
        raise error_type(f"{SECRET} {RAW} {request.url}")

    with (
        caplog.at_level(logging.DEBUG),
        client(handler, provider=provider, shared=shared) as service,
    ):
        exc = assert_code(
            "network_failure" if error_type is httpx.ConnectError else "timeout",
            lambda: service.request_json("GET", PATH if provider == "courtlistener" else GROQ_PATH),
        )
    assert shared.attempts_used == (2 if provider == "courtlistener" else 1)
    assert clock.sleeps == ([0.25] if provider == "courtlistener" else [])
    assert exc.__context__ is None
    assert exc.__cause__ is None
    rendered = "".join(traceback.format_exception(exc))
    assert SECRET not in rendered and RAW not in rendered
    assert SECRET not in caplog.text and RAW not in caplog.text


@pytest.mark.parametrize(
    "error_type",
    [httpx.ReadError, httpx.WriteError, httpx.RemoteProtocolError, httpx.DecodingError],
)
def test_other_network_errors_do_not_retry(error_type, clock):
    def handler(_):
        raise error_type(RAW)

    with client(handler) as service:
        assert_code(
            "network_failure"
            if error_type in (httpx.ReadError, httpx.WriteError)
            else "invalid_response",
            lambda: service.request_json("GET", PATH),
        )
        assert service.budget.attempts_used == 1
    assert not clock.sleeps


@pytest.mark.parametrize("header", ["30", "20", "9999999999999999999999999999999999999"])
def test_retry_after_too_long_does_not_sleep(header, clock):
    with client(lambda _: httpx.Response(429, headers={"Retry-After": header})) as service:
        assert_code("rate_limited", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 1
    assert clock.sleeps == []


def test_retry_after_review_budget_too_short(clock):
    with client(
        lambda _: httpx.Response(503, headers={"Retry-After": "3"}),
        shared=ProviderBudget(clock.now + 2),
    ) as service:
        assert_code("rate_limited", lambda: service.request_json("GET", PATH))
    assert clock.sleeps == []


@pytest.mark.parametrize(
    "header,wait",
    [("2", 2.0), ("0", 0), ("garbage", 0.25), ("-1", 0.25), ("nan", 0.25), ("1.5", 0.25)],
)
def test_retry_after_seconds_and_malformed_fallback(header, wait, clock):
    seen = []

    def handler(_):
        seen.append(clock.now)
        return httpx.Response(
            429 if len(seen) == 1 else 200, headers={"Retry-After": header}, json={}
        )

    with client(handler) as service:
        service.request_json("GET", PATH)
    assert seen == [100, 100 + wait]
    assert clock.sleeps == ([wait] if wait else [])


@pytest.mark.parametrize("seconds", [-10, 3, 30])
def test_retry_after_http_date(seconds, clock, monkeypatch):
    fixed = datetime(2026, 10, 2, tzinfo=UTC)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(transport, "datetime", FixedDatetime)
    seen = []

    def handler(_):
        seen.append(clock.now)
        return httpx.Response(
            429 if len(seen) == 1 else 200,
            json={},
            headers={
                "Retry-After": format_datetime(fixed + timedelta(seconds=seconds), usegmt=True),
            },
        )

    with client(handler) as service:
        if seconds == 30:
            assert_code("rate_limited", lambda: service.request_json("GET", PATH))
            assert seen == [100]
        else:
            service.request_json("GET", PATH)
            assert seen == [100, 100 + max(seconds, 0)]
    assert clock.sleeps == ([seconds] if 0 < seconds < 20 else [])


@pytest.mark.parametrize("phase", ["headers", "stream", "parse", "wait"])
@pytest.mark.parametrize("review_deadline", [False, True])
def test_monotonic_deadline_checks(phase, review_deadline, clock, monkeypatch):
    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"ok":'
            clock.now += 3
            yield b"true}"

    def handler(request):
        assert all(0 < value <= 2 for value in request.extensions["timeout"].values())
        if phase == "headers":
            clock.now += 3
        if phase == "wait":
            return httpx.Response(429, headers={"Retry-After": "1"})
        if phase == "stream":
            return httpx.Response(200, stream=SlowStream())
        return httpx.Response(200, json={})

    if phase == "parse":
        loads = transport.json.loads

        def slow_loads(body):
            clock.now += 3
            return loads(body)

        monkeypatch.setattr(transport.json, "loads", slow_loads)
    if phase == "wait":
        monkeypatch.setattr(transport.time, "sleep", lambda _: setattr(clock, "now", 103))
    shared = ProviderBudget(clock.now + (2 if review_deadline else 90))
    with client(handler, shared=shared, policy=ProviderPolicy(call_timeout=2)) as service:
        exc = assert_code(
            "deadline_exceeded" if review_deadline else "timeout",
            lambda: service.request_json("GET", PATH),
        )
    assert isinstance(exc, ProviderDeadline) == review_deadline
    assert shared.attempts_used == 1


def test_expired_budget_sends_nothing(clock):
    with client(
        lambda _: pytest.fail("HTTP must not run"), shared=ProviderBudget(clock.now)
    ) as service:
        assert_code("deadline_exceeded", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 0


@pytest.mark.parametrize("kind", ["body", "params", "path"])
def test_request_size_bounds(kind):
    policy = ProviderPolicy(max_request_bytes=80)
    with client(lambda _: pytest.fail("HTTP must not run"), policy=policy) as service:
        assert_code(
            "request_too_large",
            lambda: service.request_json(
                "POST",
                PATH + ("a" * 81 if kind == "path" else ""),
                {"raw": "x" * 81} if kind == "body" else {},
                params={"q": "x" * 81} if kind == "params" else None,
            ),
        )
        assert service.budget.attempts_used == 0


class Chunks(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False
        self.reads = 0

    def __iter__(self):
        for chunk in self.chunks:
            self.reads += 1
            yield chunk

    def close(self):
        self.closed = True


@pytest.mark.parametrize("kind", ["length", "stream", "compressed", "exact"])
def test_response_size_and_stream_cleanup(kind):
    headers = {}
    chunks = [b'"', b"x" * 64, b'"']
    expected = "response_too_large"
    if kind == "length":
        headers["Content-Length"] = "65"
    if kind == "compressed":
        compressed = gzip.compress(b'"' + b"x" * 1024 + b'"')
        assert len(compressed) < 64
        chunks = [compressed]
        headers = {"Content-Encoding": "gzip", "Content-Length": str(len(compressed))}
    if kind == "exact":
        chunks = [b'"' + b"x" * 62 + b'"']
    stream = Chunks(chunks)
    with client(
        lambda _: httpx.Response(200, headers=headers, stream=stream),
        policy=ProviderPolicy(max_response_bytes=64),
    ) as service:
        if kind == "exact":
            assert service.request_json("GET", PATH) == "x" * 62
        else:
            assert_code(expected, lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 1
    assert stream.closed
    if kind == "length":
        assert stream.reads == 0
    if kind == "stream":
        assert stream.reads == 2


@pytest.mark.parametrize("length", ["abc", "-1", "4,4"])
def test_malformed_content_length(length):
    with client(lambda _: httpx.Response(200, headers={"Content-Length": length}, json={})) as svc:
        assert_code("invalid_response", lambda: svc.request_json("GET", PATH))


@pytest.mark.parametrize("body", [b"not-json", b'{"secret":', b"\xff", b""])
def test_json_failures_no_retry_or_raw_exception(body, clock):
    with client(lambda _: httpx.Response(200, content=body)) as service:
        exc = assert_code("invalid_response", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 1
    assert exc.__context__ is None
    assert not clock.sleeps


@pytest.mark.parametrize(
    "field,value",
    [
        ("call_timeout", math.nan),
        ("call_timeout", math.inf),
        ("call_timeout", 0),
        ("call_timeout", 21),
        ("call_timeout", True),
        ("max_concurrency", 3),
        ("max_concurrency", 0),
        ("max_concurrency", 1.0),
        ("courtlistener_retries", 2),
        ("groq_retries", 1),
        ("retry_base", 3),
        ("retry_cap", math.inf),
        ("max_request_bytes", 128 * 1024 + 1),
        ("max_response_bytes", 4 * 1024 * 1024 + 1),
        ("max_request_bytes", -1),
        ("max_response_bytes", True),
    ],
)
def test_invalid_policy(field, value):
    assert_code("invalid_policy", lambda: ProviderPolicy(**{field: value}))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"deadline": math.nan},
        {"deadline": math.inf},
        {"deadline": True},
        {"max_attempts": 61},
        {"max_attempts": -1},
        {"max_attempts": True},
        {"attempts_used": -1},
        {"attempts_used": 61},
    ],
)
def test_invalid_budget(kwargs):
    values = {"deadline": time.monotonic() + 90, **kwargs}
    assert_code("invalid_policy", lambda: ProviderBudget(**values))


def test_zero_attempts_preserves_local_deadline_but_blocks_network():
    shared = budget(max_attempts=0)
    assert shared.remaining() > 0
    assert_code("request_budget_exhausted", shared.reserve)
    with client(lambda _: pytest.fail("HTTP must not run"), shared=shared) as service:
        assert_code("request_budget_exhausted", lambda: service.request_json("GET", PATH))
    assert shared.attempts_used == 0


@pytest.mark.parametrize(
    "provider,credential",
    [
        ("other", SECRET),
        ("groq", ""),
        ("groq", "secret\r\nheader"),
        ("groq", "é"),
        ("groq", "x" * 4097),
    ],
)
def test_invalid_provider_or_credentials(provider, credential):
    assert_code("invalid_request", lambda: BoundedProviderClient(provider, credential, budget()))


def test_sanitized_unknown_error_code():
    assert str(ProviderUnavailable(RAW)) == "provider_unavailable"
    assert repr(ProviderUnavailable([RAW])) == "ProviderUnavailable('provider_unavailable')"


def test_client_context_closes_owned_transport():
    class OwnedTransport(httpx.MockTransport):
        closed = False

        def close(self):
            self.closed = True

    owned = OwnedTransport(lambda _: httpx.Response(200, json={}))
    with BoundedProviderClient("groq", SECRET, budget(), transport=owned) as service:
        service.request_json("POST", GROQ_PATH, {})
    assert owned.closed
    assert_code("client_closed", lambda: service.request_json("POST", GROQ_PATH, {}))
    assert_code("client_closed", service.__enter__)


def test_shared_concurrency_across_clients_and_slot_release():
    shared = budget()
    lock = threading.Lock()
    entered = threading.Event()
    release = threading.Event()
    active = 0
    peak = 0
    seen = 0

    def handler(_):
        nonlocal active, peak, seen
        with lock:
            active += 1
            seen += 1
            peak = max(peak, active)
            if active == 2:
                entered.set()
        try:
            assert release.wait(3)
            return httpx.Response(200, json={})
        finally:
            with lock:
                active -= 1

    with client(handler, shared=shared) as first, client(handler, shared=shared) as second:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [
                pool.submit((first if i % 2 else second).request_json, "GET", PATH)
                for i in range(6)
            ]
            try:
                assert entered.wait(3)
                with lock:
                    assert seen == active == 2
            finally:
                release.set()
            assert all(future.result(timeout=3) == {} for future in futures)
    assert peak == 2
    assert seen == shared.attempts_used == 6


def test_semaphore_wait_in_call_deadline():
    shared = budget()
    assert shared._slots.acquire(blocking=False)
    assert shared._slots.acquire(blocking=False)
    with client(
        lambda _: pytest.fail("HTTP must not run"),
        shared=shared,
        policy=ProviderPolicy(call_timeout=0.02),
    ) as service:
        try:
            assert_code("timeout", lambda: service.request_json("GET", PATH))
            assert shared.attempts_used == 0
        finally:
            shared._slots.release()
            shared._slots.release()


def test_semaphore_wait_in_review_deadline():
    shared = ProviderBudget(time.monotonic() + 0.02)
    shared._slots.acquire()
    shared._slots.acquire()
    with client(lambda _: pytest.fail("HTTP must not run"), shared=shared) as service:
        try:
            assert_code("deadline_exceeded", lambda: service.request_json("GET", PATH))
            assert shared.attempts_used == 0
        finally:
            shared._slots.release()
            shared._slots.release()


def test_failure_releases_semaphore():
    with client(lambda _: httpx.Response(404)) as service:
        for _ in range(4):
            assert_code("http_failure", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 4


def test_http_logging_outside_boundary_remains_enabled(caplog):
    with caplog.at_level(logging.INFO), client(lambda _: httpx.Response(200, json={})) as svc:
        svc.request_json("GET", PATH)
        assert not caplog.records
        logging.getLogger("httpx").info("outside-boundary-record")
    assert caplog.messages == ["outside-boundary-record"]


def test_provider_cookies_are_not_replayed(clock):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            503 if len(seen) == 1 else 200,
            json={},
            headers={"Set-Cookie": "private=synthetic; Path=/"},
        )

    with client(handler) as service:
        service.request_json("GET", PATH)
        service.request_json("GET", PATH)
    assert len(seen) == 3
    assert all("cookie" not in request.headers for request in seen)


def test_courtlistener_retry_can_be_disabled(clock):
    with client(
        lambda _: httpx.Response(503), policy=ProviderPolicy(courtlistener_retries=0)
    ) as service:
        assert_code("http_failure", lambda: service.request_json("GET", PATH))
        assert service.budget.attempts_used == 1
    assert not clock.sleeps


def test_lower_client_concurrency_with_shared_budget():
    shared = budget()
    entered = threading.Event()
    release = threading.Event()
    lock = threading.Lock()
    seen = 0

    def handler(_):
        nonlocal seen
        with lock:
            seen += 1
            entered.set()
        assert release.wait(3)
        return httpx.Response(200, json={})

    with client(handler, shared=shared, policy=ProviderPolicy(max_concurrency=1)) as svc:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(svc.request_json, "GET", PATH)
            second = pool.submit(svc.request_json, "GET", PATH)
            try:
                assert entered.wait(3)
                with lock:
                    assert seen == 1
            finally:
                release.set()
            assert first.result(timeout=3) == second.result(timeout=3) == {}
    assert seen == shared.attempts_used == 2


def test_default_size_limits_reject_large_request_and_response():
    with client(lambda _: pytest.fail("HTTP must not run")) as service:
        assert_code(
            "request_too_large",
            lambda: service.request_json(
                "POST",
                PATH,
                {"text": "x" * (128 * 1024)},
            ),
        )
    stream = Chunks([b"x" * (4 * 1024 * 1024), b"x"])
    with client(lambda _: httpx.Response(200, stream=stream)) as service:
        assert_code("response_too_large", lambda: service.request_json("GET", PATH))
    assert stream.closed


def test_deadline_during_failed_response_cleanup_strips_raw_context(clock):
    class ExpiringCleanup(Chunks):
        def close(self):
            super().close()
            clock.now += 100

    stream = ExpiringCleanup([RAW.encode()])
    with client(lambda _: httpx.Response(200, stream=stream)) as service:
        exc = assert_code("deadline_exceeded", lambda: service.request_json("GET", PATH))
    assert exc.__context__ is None
    assert exc.__cause__ is None
    assert RAW not in "".join(traceback.format_exception(exc))
    assert stream.closed
