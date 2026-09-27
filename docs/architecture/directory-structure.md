# Directory and ownership guide

All feature folders are placeholders with responsibility notes. Their existence
does not indicate completed functionality. Work is tracked only in root TODO.md.

```text
FilingGuard AI/
|-- FilingGuard_AI_SRS.md       Original requirements
|-- TODO.md                    Ordered implementation and acceptance checklist
|-- README.md                  Setup and current scaffold status
|-- package.json               npm workspace and backend helper commands
|-- .env.example               Local PostgreSQL values
|-- apps/
|   |-- web/
|   |   |-- package.json       Frontend dependencies
|   |   |-- vite.config.ts     Plugins and development API proxy
|   |   |-- tsconfig.json      Strict TypeScript configuration
|   |   |-- .env.example       Public browser configuration only
|   |   |-- public/            Public static assets
|   |   `-- src/
|   |       |-- app/           Router, providers, app composition
|   |       |-- assets/        Imported frontend assets
|   |       |-- components/
|   |       |   |-- layout/    Navigation and shared page structure
|   |       |   `-- ui/        Reusable UI primitives
|   |       |-- features/
|   |       |   |-- intake/
|   |       |   |-- analyses/
|   |       |   |-- findings/
|   |       |   |-- claim-authority-graph/
|   |       |   |-- reports/
|   |       |   |-- red-team/       P1
|   |       |   `-- grounded-qa/    P1
|   |       |-- lib/api/       API wrapper and generated schema declarations
|   |       |-- styles/        Shared CSS and library imports
|   |       `-- test/          Test helpers
|   `-- api/
|       |-- pyproject.toml     Python dependencies and tool configuration
|       |-- .env.example      Private backend configuration template
|       |-- migrations/versions/
|       |-- scripts/           API-local helpers such as OpenAPI export
|       |-- src/filingguard/
|       |   |-- main.py        Application factory; health endpoint only
|       |   |-- api/routes/    Thin HTTP handlers
|       |   |-- core/          Config, errors, logging and access helpers
|       |   |-- db/models/     SQLAlchemy persistence (planned)
|       |   |-- integrations/
|       |   |   |-- courtlistener/
|       |   |   |-- llm/
|       |   |   `-- storage/
|       |   |-- modules/
|       |   |   |-- analyses/      Pipeline coordination
|       |   |   |-- documents/     Parsing and locations
|       |   |   |-- citations/     Extraction and authority identity
|       |   |   |-- claims/        Proposition extraction and links
|       |   |   |-- propositions/  Grounded support classification
|       |   |   |-- quotes/        Exact/normalized/fuzzy checks
|       |   |   |-- court_rules/   Profile applicability and disclosure
|       |   |   |-- privacy/       Local detection and masking
|       |   |   |-- scoring/       Deterministic score and coverage
|       |   |   |-- evidence/      Locations, sources and provenance
|       |   |   |-- reports/       Saved-result exports
|       |   |   |-- red_team/      P1
|       |   |   |-- grounded_qa/   P1
|       |   |   `-- table_of_authorities/  P2
|       |   `-- resources/
|       |       |-- courts/     Versioned profile data
|       |       |-- prompts/    Versioned prompt templates
|       |       `-- reports/    Export templates
|       `-- tests/
|           |-- unit/
|           `-- integration/
|-- contracts/                Generated OpenAPI contract
|-- data/demo/
|   |-- filings/              Synthetic sample input
|   |-- authorities/          Synthetic or attributed public source fixtures
|   `-- expected/             Expected results, separately validated
|-- docs/
|   |-- architecture/
|   |-- product/
|   `-- delivery/
|-- infra/                    Local DB and future deployment configuration
|-- scripts/                  Cross-project utilities
`-- tests/e2e/                End-to-end user journeys
```

## Placement rules

Put user-workflow UI code inside its frontend feature. Reuse `components/ui` for
generic controls only. Feature tests should sit beside their components; shared
browser test support goes in `src/test`.

On the backend, routes call services; the analysis service composes modules.
Provider adapters own request/auth/error details. Feature modules own analysis
decisions. Scoring and quote matching should remain independently testable.

Keep Pydantic response schemas near their owner. Put SQLAlchemy models in
`db/models`, not in browser contracts. OpenAPI generates the browser-facing types.
Keep legal rule and prompt versions in resources; never hardcode court rules into
UI controls. Test fixtures are versioned separately from private runtime storage.

Create `schemas.py`, `service.py` and any additional helper files when implementing
the corresponding task. The scaffold does not create dozens of empty code files
with invented interfaces. Add `__init__.py` when turning a feature into a package.
