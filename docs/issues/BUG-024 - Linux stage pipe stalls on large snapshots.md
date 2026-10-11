---
type: issue
status: resolved
date: 2026-10-11
tags: [issues, execution, ci]
---
# Linux stage pipe stalls on large snapshots

## Symptom and impact

GitHub Checks run `38147439448` passes 712 API controls but fails two cached-demo
integration controls: the quote stage times out after 30 seconds and saves
unavailable coverage. The same two failures reproduce in isolated Linux with the
committed `10b1a6d` checkout and locked dependencies. Windows passes these controls.
No real filing or provider credential is used in reproduction.

## Cause

The parent used `communicate(payload, timeout=.1)` then retried with `None`.
CPython 3.12's POSIX implementation registers stdin for writing only when the
current input argument is nonempty. If worker startup exceeds the first poll and
the payload exceeds pipe capacity, remaining bytes and EOF never reach the worker.
It waits on input until the independent hard deadline terminates the process tree.
Contained native quote comparison itself completes in milliseconds in Linux.

## Fix and regression check

Use one `communicate(payload, timeout=remaining)` call. The independent watcher
still kills the process tree on shutdown and deadline, including Windows stdin
write blocking. Memory/CPU limits, snapshot bounds, quotas and verdict rules remain
unchanged. Add a real contained-worker regression with 300 ms startup delay and
100,000-character input; it fails on the old Linux code with a five-second deadline.
The affected integration suite passes all 21 controls on Windows and Linux after
correction, including the two former failures, cutoff, shutdown and descendant
cleanup. Fresh GitHub CI is still required before closing the release gate.

[[TODO]] T024/T057/T059, [[docs/issues/Index]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[docs/sessions/2026-10-11 - Release checkpoint publication]].
