# Retrieval entry-route evaluations, 2026-09-27

Eight fresh gpt-6-astra sessions completed against the frozen seven-node synthetic
corpus. Parent-Codex trace review found all eight answers supported by the available
evidence and all code/knowledge stores unchanged. This is answer and workflow review,
not a private coding grader or a blind human evaluation.

| Case | Observed route and outcome | Review |
| --- | --- | --- |
| Useful metadata | storage tag returned the archive constraint; graph expansion and further content search informed the answer. | Pass |
| Missing tag | retries returned zero; agent removed the filter and found the partner charging rule. | Pass |
| Weak metadata | retry returned a timing rule; agent searched beyond that tag and explained why timing does not establish charge safety. | Pass |
| Detailed question | Direct semantic query, no guessed tag; found non-idempotency inside Partner agreement and advised reconciliation. | Pass |
| Source anchor | Looked up writer.py, searched content, expanded and read the archive/restoration obligations. | Pass |
| Unobvious title | Found Continuity rehearsal and included its restore gate; semantic search had already delivered it before graph expansion. | Pass |
| Wrong type | decision filter missed the relevant constraint; agent removed it and found tenant-aware cache keys. | Pass |
| No evidence | Broadened queries across repositories/statuses and reported missing approval evidence without inventing an algorithm. | Pass |

All agents read the dedicated retrieval skill. Empty-tag fallback, insufficient-tag
fallback and wrong-type broadening were actually exercised, not inferred merely
from a correct final answer. All answers preserved reported-evidence limits. The
trace JSON records query text, filters, returned records, reads, graph context,
final answers, native usage and evaluator evidence indexes.

## Semantic calibration

Before reviewing agent behavior, the pinned all-MiniLM-L6-v2 model ranked every
required target within the top three for the seven cases with known answers. The
no-evidence case intentionally has no correct target. Calibration used each task's
text without tag/type restrictions; it measures retrieval ranks, not agent judgment.
The reusable calibration helper reproduced the recorded ranks and metadata.

This corpus has only seven nodes, fewer than the default search limit of ten, so
unfiltered agent searches returned the entire corpus. The trials establish basic
routing, evidence interpretation and restraint. They do not establish large-store
recall, an incremental graph benefit, or superiority over direct semantic search.
No titles, tags, targets, prompts or criteria were tuned after outcomes were observed.

## Integrity and limitations

The preparation/skill/policy hashes match the frozen experiment. Both Git heads and
working-tree status remained unchanged in every trial; no proposal branches or
native file-change events occurred. No knowledge-authoring commands were observed.
Synchronization and derived-index updates were allowed. No retries or quota failures
occurred. Each case ran once with scoped Docker mounts and a 600-second wall budget.
The image identity and model declaration are preserved in the machine report.

Knowledge CLI calls (including synchronization/help) ranged from three to nine;
actor durations ranged from about 48 to 63 seconds. These costs are observations,
not a controlled comparison with the previous policy. Native usage is retained
rather than estimating productivity from successful answers.

Three automated fixture/report tests passed. They also verify that successful actor
exit/self-reported success does not become an answer pass without evaluator review,
and an explicit negative evaluator judgment is retained as failure.

[Machine report](retrieval-routes-astra-20260927.json) ·
[Protocol and reproduction](../retrieval-route-evaluation.md)
