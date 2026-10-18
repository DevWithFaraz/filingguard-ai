# claim-authority-graph

P0: section/claim/authority graph and accessible equivalent list. T048-T049.

Implemented in [[apps/web/src/features/analyses/README]] using persisted graph
nodes/links from the private API. React Flow bounds the visual view to 200 nodes;
the keyboard list retains every substantive relationship. Selection opens related
saved findings. No hardcoded graph or independent legal/scoring logic is used.
Use shared API types/client from src/lib/api. Display backend statuses faithfully;
do not duplicate legal analysis or scoring logic in the browser.

Per T105 (FR-105, FR-106, FR-064):
- Interactive viewport toolbar supports zoom in, zoom out, fit-to-view, and reset (FR-105).
- Unsupported claims render as separate warning nodes with distinct red warning borders,
  backgrounds, and `⚠️ [Warning: Unsupported claim]` labels in both visual canvas and
  keyboard-accessible list (FR-106).
- Multiple claims citing a single authority (FR-064) share an authority node and display
  associated claim count, citing claim jump buttons, and cross-view finding selection.
- Bi-directional cross-view selection synchronizes findings inspection and graph node highlights
  without losing finding context.

