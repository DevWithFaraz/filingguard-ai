# Shared API contract

Pydantic/FastAPI owns the schema. Run `npm run contracts:export`, then
`npm run contracts:generate` after installing dependencies. Commit the OpenAPI JSON
and generated browser declarations with endpoint changes; do not edit generated
types by hand. Only the health endpoint exists in the current scaffold.
