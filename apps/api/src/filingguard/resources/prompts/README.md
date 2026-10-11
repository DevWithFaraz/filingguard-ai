# Prompt resources

`proposition_v1.py` owns the reviewed `proposition-source-review-v3` system prompt.
It treats filing and source text as untrusted data, uses bounded passages with IDs,
requires exact original-source evidence, considers qualifications and distinguishes
uncertainty from substantive support. The Groq adapter binds this prompt directly;
callers cannot replace it. Model/prompt/method versions accompany stored evidence.
Red-team and finding-Q&A prompts remain P1.
The model returns allowlisted immutable source evidence-unit IDs only. The adapter
binds exact original excerpts, source hashes and absolute spans locally. Every selected
passage character is transmitted once in ordered bounded units; context is retained.
Unknown or duplicate IDs remain unavailable. Offline schema/binding verification does
not establish live semantic accuracy.

Related: [[apps/api/src/filingguard/integrations/llm/README]],
[[apps/api/src/filingguard/modules/propositions/README]], [[TODO]].
