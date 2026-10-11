---
type: issue
status: resolved
date: 2026-09-27
tags: [courtlistener, fixtures, provenance]
---
# First opinion reference can be a dissent

## Observed behavior and cause

During T014 source preparation, Miranda cluster 107252 returned opinion 9423235
first. Its provider type was 040dissent and its opening identified Justice White
as dissenting. Taking sub_opinions[0] would wrongly use a dissent for the intended
majority-summary control. A successful citation lookup does not identify which
opinion supplies the Court's holding.

## Fix and evidence

The preparation tool selects the smallest referenced opinion ID and requires a
010combined or 020lead type, otherwise fails closed. A fresh fetch selected
107252, type 010combined, with the majority text present. The retained
[[data/demo/curated-v1/README|fixture]] records this provenance and exact relevant
source spans. This heuristic is narrowly bounded preparation code, not sufficient
for a production adapter; T034 must handle opinion selection deliberately.
Combined text still contains dissents; type validation alone does not establish
the role of every passage. The fixture tests check retained source types.

No public analysis was enabled and no legal verdict was issued from the initial
dissent snapshot. It was replaced before locking draft expectations.

[[docs/issues/Index]], [[TODO]], [[apps/api/src/filingguard/integrations/courtlistener/README]].
