# End-to-end acceptance

T007 configures Playwright; T052 exercises sample -> intake -> progress -> findings
-> graph -> evidence -> report. Test keyboard flow, desktop/mobile layout, provider
failure and two-session isolation. Use deterministic demo fixtures for CI. Run a
separate deployed live smoke test before submission.

Implemented shell checks in shell.spec.ts cover live health, disabled intake,
keyboard skip navigation, routes, desktop/mobile width, failure and retry.
Playwright starts local API/UI processes and stops those it owns after testing.
No legal-analysis acceptance or session isolation tests exist yet.
