# HTTP routes

Only health is implemented. Add thin routes for analyses, findings, graph, courts,
reports and deletion. Validate requests with Pydantic, enforce session ownership
and delegate to modules. Do not put provider calls or scoring logic in handlers.
