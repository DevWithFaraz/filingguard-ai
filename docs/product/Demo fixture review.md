---
type: review
status: assistant-reviewed-with-conditions
date: 2026-09-27
tags: [demo, evidence, acceptance]
---
# Demo fixture review

T014 material: [[data/demo/curated-v1/README]]. T015 is complete under the user's
explicit delegation of review to Codex on September 27, 2026. Reviewer: Codex,
an AI assistant. This replaces the planned user review for this task; no human
or legal-expert review is claimed. No further user approval is required.
The file `data/demo/curated-v1/expectations.json` links every scenario to the exact
filing span and, where applicable, a source span. Verdict: accepted for controlled
demo development, with 13 scenarios accepted and five conditional judgments below.
These are reviewed expectations, not observed engine output or an accuracy benchmark.

## Review the content

1. Brown's benign paragraph summarizes its equal-protection conclusion for racial
   segregation in public education. The exact quote ends with "inherently unequal."
2. Miranda's benign paragraph is limited to custodial interrogation, not every
   encounter. Source text warns before questioning of silence and attorney rights.
3. Obergefell's benign paragraph summarizes the majority's right-to-marry holding.
   Its retained source span includes the original newline, not a rewritten quote.
4. The second Brown paragraph deliberately reverses the holding and changes
   "unequal" to "equal" in the quotation. Review these as separate claim/quote tests.
5. Example v. Imaginary Agency is explicitly invented; offline not-found must not
   be presented as an observed live result or generalized proof of fabrication.
6. Privacy issues are entirely invented: invalid-range SSN shape, contextual full
   date of birth and contextual bank account. The administrative event date is a
   benign control; citation volumes/pages/years must not become account findings.
7. Missing disclosure is conditional on AI-used=true and a synthetic required
   disclosure profile. AI-used=false tests inapplicability, not compliance.
8. Timeout and unavailable-source variants must remain unavailable/insufficient,
   not verified, supported or not-found.

## Scenario judgments

Accepted: citation-brown, citation-miranda, citation-obergefell, brown-supported,
miranda-supported, obergefell-supported, brown-misrepresented, quote-exact,
privacy-dob, privacy-account, benign-event-date, source-unavailable and
lookup-unavailable. The majority passages and surrounding context support the
three case summaries and the reversed Brown claim. All 18 filing/source spans
and all three stored text hashes matched. Miranda is scoped to custodial
interrogation and must retain its waiver/context qualifications; these summaries
do not claim to exhaust subsequent case law. The Obergefell passage is in the
majority opinion (slip page 22), not the syllabus or a dissent.

Five conditional judgments:

1. citation-unresolved: not_found is accepted only for the explicit offline stub.
   No actual provider response to the invented citation was measured. A real
   parser may reject this input; do not call it proven live hallucination detection.
2. quote-altered: confirmed absent from the Brown snapshot and reversed in meaning.
   RapidFuzz fuzz.ratio is 98.148148% for the paired sentences. Close is provisional
   until a matcher/threshold is versioned; not_found is defensible for a stricter
   matcher. Exact/normalized is unacceptable. High similarity cannot suppress review.
3. privacy-ssn: accepted as an SSN-shaped signal, not a valid issued SSN. The
   deliberately invalid prefix makes this a pattern test, not a valid-SSN test.
4. disclosure-omitted: accepted only with ai_used=true and an available synthetic
   profile requiring the absent certification. Until T028 supplies that profile,
   this is a planned scenario. Missing/unsupported profiles must be unavailable.
5. disclosure-not-applicable: skip the specific AI-disclosure rule when ai_used=false
   makes it inapplicable. Do not skip unrelated applicable rules or the whole stage.

The benign event date is explicitly described as not a birth date, so proximity
to the words "birth date" must not override their negation. Filing headings reveal
the answers; this is an explanatory demo, unsuitable for blind model evaluation.
Use unlabeled held-out material before reporting accuracy. The one-page PDF also
does not establish multi-page, scanned or encrypted-document handling.

## Review identity and integration

This review applies to these SHA-256 hashes of original bytes:

- filing.txt: `063bab93cf24bcc22f570ade751c346e3cdd283c7ff6544e28e0f7a20a9f8e18`
- filing.pdf: `ed064070abb28a7fadebefb40290085128e58124b7367270e8907af620849916`
- expectations.json: `5854d64c902d38035d23ce03d8678a4cd063e97709e76413b4321ffef897df83`
- scenarios.json: `0b6c886d0abc518f21287ee238746c3ff96af7f48e23785467f7ebc263062736`
- sources.json: `39fc1e090f0c355537550bd4e3e6b813b03dac8f5d418b10ca5200f2d3c49209`

The original manifest/draft metadata still says awaiting_human_review. This note
records completed delegated AI review without inventing human review. T016 must
represent that provenance explicitly and apply these conditions before replay;
the current runtime gate was not changed in this review-only turn. Content changes
require checking affected judgments again. No Groq generation or engine execution
was performed. Source IDs, URLs and individual hashes remain in sources.json.

External corroboration: [Brown transcript, National Archives](https://www.archives.gov/milestone-documents/brown-v-board-of-education)
and [Obergefell opinion, Cornell LII](https://www.law.cornell.edu/supremecourt/text/14-556).
The retained CourtListener majority passages are the direct fixture evidence.

[[docs/product/Features]], [[docs/sessions/Index]], [[FilingGuard_AI_SRS#18.2 Demo Acceptance Test]].
