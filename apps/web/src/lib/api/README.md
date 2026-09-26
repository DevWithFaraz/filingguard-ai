# Browser API boundary

Generate `schema.d.ts` from `contracts/openapi.json` using root npm commands.
Add a small fetch wrapper for origin, session credentials, request IDs and typed
errors. Feature hooks own query keys/polling. No browser-side OpenAI/CourtListener
keys or direct provider calls. Generated files do not exist until T003.
