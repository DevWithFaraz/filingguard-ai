# claim-authority-graph

P0: section/claim/authority graph and accessible equivalent list. T048-T049.

Implemented in [[apps/web/src/features/analyses/README]] using persisted graph
nodes/links from the private API. React Flow bounds the visual view to 200 nodes;
the keyboard list retains every substantive relationship. Selection opens related
saved findings. No hardcoded graph or independent legal/scoring logic is used.
Use shared API types/client from src/lib/api. Display backend statuses faithfully;
do not duplicate legal analysis or scoring logic in the browser.
