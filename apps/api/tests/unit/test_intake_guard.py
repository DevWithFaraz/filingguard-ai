from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from filingguard.core.admission import Admission, IntakeGuard
from filingguard.core.config import Settings


@pytest.mark.parametrize("case", ["chunked", "disconnect", "negative", "huge", "valid", "timeout"])
async def test_body_budget_and_disconnect_release_slot(tmp_path, monkeypatch, case):
    admission = Admission()
    settings = Settings(intake_enabled=True, private_storage_directory=tmp_path / "private")
    app = SimpleNamespace(state=SimpleNamespace(admission=admission))
    monkeypatch.setattr(
        "filingguard.core.admission.authenticate", lambda _: ("a" * 64, datetime.now(UTC))
    )
    messages, called = [], []
    incoming = (
        [{"type": "http.disconnect"}]
        if case == "disconnect"
        else [
            {"type": "http.request", "body": b"x" * 400000, "more_body": True},
            {"type": "http.request", "body": b"x" * 400000, "more_body": False},
        ]
        if case == "chunked"
        else [{"type": "http.request", "body": b"ok", "more_body": False}]
    )

    async def receive():
        if case == "timeout":
            raise TimeoutError()
        return incoming.pop(0)

    async def send(message):
        messages.append(message)

    async def downstream(scope, receive, send):
        called.append((await receive())["body"])

    headers = []
    if case in {"negative", "huge"}:
        headers = [(b"content-length", b"-1" if case == "negative" else b"9" * 5000)]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/analyses/text",
        "headers": headers,
        "app": app,
    }
    await IntakeGuard(downstream, settings)(scope, receive, send)
    assert admission.slot.acquire(blocking=False)
    admission.slot.release()
    if case == "valid":
        assert called == [b"ok"]
    else:
        assert not called
        if case != "disconnect":
            assert messages[0]["status"] == (408 if case == "timeout" else 413)
            assert (b"cache-control", b"no-store") in messages[0]["headers"]


def test_rate_buckets_fail_closed_at_capacity_and_expire(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("filingguard.core.admission.time.monotonic", lambda: now[0])
    admission = Admission()
    for index in range(1024):
        admission.limit(str(index), count=1, window=60)
    with pytest.raises(OverflowError):
        admission.limit("overflow", count=1, window=60)
    with pytest.raises(OverflowError):
        admission.limit("0", count=1, window=60)
    now[0] = 61
    admission.limit("new", count=1, window=60)
    assert len(admission._buckets) == 1
