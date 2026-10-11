# Shared infrastructure

`config.py` owns typed opt-in intake/provider flags, stage/overall deadlines and
private storage configuration. Defaults keep public intake and external stages
closed. Session ownership, typed errors, redacted logging and limits are implemented
in their route/module boundaries. Liveness works without credentials; the separate
readiness route fails closed for missing enabled-provider credentials, schema,
storage/cleanup and exact-origin configuration. It does not prove provider
availability or hosted containment. See [[apps/api/src/filingguard/api/routes/README]],
[[docs/delivery/Deployment guide]] and [[TODO]] T057.
