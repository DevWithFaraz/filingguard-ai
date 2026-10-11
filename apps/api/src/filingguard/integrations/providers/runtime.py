"""Shared monotonic deadline and request quota for one review."""

import math
import time
from dataclasses import dataclass, field
from threading import BoundedSemaphore, Lock

_CODES = frozenset(
    {
        "provider_unavailable",
        "deadline_exceeded",
        "request_budget_exhausted",
        "invalid_request",
        "invalid_policy",
        "request_too_large",
        "response_too_large",
        "rate_limited",
        "http_failure",
        "network_failure",
        "timeout",
        "invalid_response",
        "client_closed",
    }
)


class ProviderUnavailable(Exception):
    """Only a fixed, bounded code crosses the provider boundary."""

    def __init__(self, code: str = "provider_unavailable") -> None:
        self.code = code if isinstance(code, str) and code in _CODES else "provider_unavailable"
        super().__init__(self.code)


class ProviderDeadline(ProviderUnavailable):
    def __init__(self) -> None:
        super().__init__("deadline_exceeded")


@dataclass
class ProviderBudget:
    deadline: float
    max_attempts: int = 60
    attempts_used: int = 0
    _lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)
    _slots: BoundedSemaphore = field(
        default_factory=lambda: BoundedSemaphore(2),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if (
            type(self.deadline) not in (int, float)
            or not math.isfinite(self.deadline)
            or type(self.max_attempts) is not int
            or not 0 <= self.max_attempts <= 60
            or type(self.attempts_used) is not int
            or not 0 <= self.attempts_used <= self.max_attempts
        ):
            raise ProviderUnavailable("invalid_policy")

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ProviderDeadline()
        return remaining

    def reserve(self) -> None:
        with self._lock:
            self.remaining()
            if self.attempts_used >= self.max_attempts:
                raise ProviderUnavailable("request_budget_exhausted")
            self.attempts_used += 1
