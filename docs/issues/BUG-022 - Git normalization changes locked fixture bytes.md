---
type: issue
status: resolved-locally
date: 2026-10-11
tags: [issues, fixtures, release]
---
# Git normalization changes locked fixture bytes

During authorized release staging, the existing `* text=auto eol=lf` rule and
Windows `core.autocrlf=true` normalized fixture JSON. A byte comparison against
the index failed for `data/demo/curated-v1/pdf-extraction.json`. The demo's review
receipt hashes exact bytes, so a checkout could reject an otherwise intact fixture.
This was caught before publication; no hosted failure is claimed.

Extend existing `.gitattributes` with `data/demo/curated-v1/** -text -whitespace`
and restage those files with `git add --renormalize`. Preserve exact supplied license
texts the same way; authored code keeps its normal text rules. Do not trim public
opinion whitespace or recalculate hashes to hide altered snapshots.

Verification: all 14 staged fixture files now equal their working-file bytes.
`.runtime/staged-fixture-receipt.json` retains filenames/hashes, without credentials.
Committed-checkpoint reproduction must load the fixture before marking T059 done.

[[TODO]] T057/T059, [[data/demo/curated-v1/README]], [[docs/issues/Index]],
[[docs/sessions/2026-10-11 - Release checkpoint publication]].
