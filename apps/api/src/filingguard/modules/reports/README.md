# reports

Priority: P0 Markdown/HTML; P1 PDF. Tasks: T051, T104 in the root TODO.md.

Render the saved analysis and evidence without reclassifying it.

Analysis snapshot in; escaped report content and downloadable export out.

`service.py` assembles owner-scoped stored results, graph, evidence, and report views.
It validates evidence snapshot hashes and exact slices before returning evidence,
masks identifiers against complete snapshots before clipping, and retains original
Unicode locations, source hashes/times and method/model/prompt metadata.
Per T102 and T104 (FR-224/225, FR-205, FR-305), exported Markdown, HTML, and
PDF reports embed an explicit 5-hop Evidence Lineage Chain (Document Span ->
Extraction Target -> Source Authority -> Verification Method -> Finding Verdict),
exact retrieved source passages with SHA-256 digests, and prominent statutory
legal assurance disclaimers.

Private terminal-analysis routes serve `/results`, `/graph`, finding `/evidence`
and `/report?format=markdown|html|pdf|graph-svg|graph-png`. Markdown, HTML, and PDF
reports embed a Claim-Authority Graph image generated from `saved_graph()` plus an
accessible node/relationship list. `graph-svg` and `graph-png` download that same
saved graph as a readable image. Active results/graph/export requests return 409;
foreign or expired analyses return 404. Exports use saved classifications without
provider calls, include score deductions/coverage/limits and evidence, and set
no-store headers. Exports include source mode and per-evidence cache/live provenance.
HTML escapes the entire report body and disallows script content. PDF export uses
ReportLab Platypus with a custom two-pass `NumberedCanvas` for exact running headers,
footers (`Page X of Y`), strict margin confinement, table wrapping, and escaping.

Graph IDs derive from stored section/claim/authority/citation/link IDs. Finding
relations connect selection to detail; the frontend offers a bounded React Flow
view and a full equivalent keyboard list. No separate demonstration graph is
substituted for stored results. Source identity and textual similarity do not
establish legal support or unchanged meaning.

Verification: scoring/report unit tests and SQLite/API tests cover output
agreement, exact evidence, tamper rejection, masking, owner isolation and escaped
HTML. Browser and hosted acceptance have separate TODO criteria. See
[[docs/decisions/ADR-011 - Grounded review and saved result boundaries]].
