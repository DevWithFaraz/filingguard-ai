---
type: issue
status: corrected-local-reverification-pending
date: 2026-10-11
tags: [issues, setup, ci]
---
# Clean checkout lacks pytest temporary parent

Fresh Git checkout `0b6d9c2` installed both locked dependency sets successfully.
Running 27 cached-demo controls then produced 15 passes and 12 setup errors:
pytest could not create `apps/api/.runtime/pytest_temp` because its ignored parent
did not exist. The regular checkout's full 712 passing tests did not expose this
dependency on a pre-existing development directory.

GitHub run `38147262802` also failed at the API test step; its exact log cause is
not yet confirmed. Do not equate a passing working-tree test with fresh CI.

`scripts/api.mjs` now creates the ignored API runtime parent before launching uv.
This preserves pytest's existing isolated basetemp and does not change application
privacy, provider flags, model retries or database schema. Verify a fresh committed
checkout and the subsequent CI run before closing the release gate.

[[TODO]] T059/T057, [[scripts/README]], [[docs/issues/Index]],
[[docs/sessions/2026-10-11 - Release checkpoint publication]].
