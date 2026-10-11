# findings

P0: filters, excerpts, evidence details and method/uncertainty labels. T047.

Implemented in [[apps/web/src/features/analyses/README]] as the shared results
screen's category/severity filters and evidence detail. It requests owner-scoped
saved findings/evidence, shows masked excerpts, source links/hash/time and actual
method/model/prompt metadata, and communicates uncertainty and human review.
Use shared API types/client from src/lib/api. Display backend statuses faithfully;
do not duplicate legal analysis or scoring logic in the browser.
