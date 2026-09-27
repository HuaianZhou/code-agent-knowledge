# Basic Memory: capture without a task-specific reminder

The Astra agent completed the historical investigation and executed the capture
workflow through standing project guidance. It submitted **zero qualifying nodes**.
This is an observed zero-write decision, not a skipped workflow or failed runner.

| Check | Observed result |
| --- | --- |
| Task request explicitly asks for capture | No |
| Standing AGENTS.md policy directs task-end capture | Yes |
| Agent reads the capture skill | Observed in native trace |
| Semantic store synchronization | Completed with pinned MiniLM; empty store |
| Actual task-end result | `zero_qualifying_candidates`, `writes: 0` |
| Knowledge main / proposals | Main unchanged; no proposals or working-tree edits |
| Held-out regression on original code | Failed with the expected missing-file error |
| Held-out regression on upstream reference fix | Passed |
| Held-out regression on actor patch | Passed |
| Independent rerun of final selected SQLite tests | 127 passed |
| Actor wall time | 278 seconds |
| Reuse comparison | Not run: no captured corpus |

The source revision was `60408ad7d53e4ec448abaf04d0bfa222aa2f8e78`. The actor received
the source tree and an attributed paraphrase of
[issue #1159](https://github.com/basicmachines-co/basic-memory/issues/1159), without
later Git history, the suggested implementation, or the held-out test. The test
comes from upstream fix `fe5f2e793535a02a8532317dd79a3162a968bef0` and exercises
actual graph and search behavior with SQLite through the local runtime.

The actor's patch supplies accepted Markdown when a file is absent and its write
status is pending or writing. Its own tests cover asynchronous acknowledgement,
relation search before materialization, later reindexing, and genuine missing-file
errors. The patch is not identical to the upstream fix. Passing this regression
does not establish equivalence across other states or preserved throughput.

## Review of the zero-write decision

The decision is reasonable for this task. Basic Memory's **pre-existing**
`docs/DOMAIN_MODEL.md` already describes materialization state, lagging asynchronous
projections, and accepted Markdown as operational authority before materialization.
The investigation applied that documented contract to a broken path.

The mere existence of newly written tests would not make all discovered rationale
redundant. The stronger evidence here is documentation that existed before the
investigation. This review does not prove that the agent considered every possible
useful claim; it supports its rejection of the central candidate.

The initially promising incident is therefore useful for testing capture restraint,
but did not produce a corpus for the planned later-task comparison. No evaluator
replacement nodes were inserted. This says nothing yet about the benefit of our
knowledge store or graph traversal in Basic Memory development.

## Limits and next selection criterion

This is one standing-policy run, not a reliability estimate, description-only skill
discovery test, or deterministic completion hook. Postgres, the full suite, and a
performance comparison were not run. The actor reported a full type-check blocker
from missing optional `pymilvus` imports; this report does not mark full type checking
as passed. Review was performed by Codex, not a blind human evaluator.

For another positive-capture candidate, first audit the historical code/docs/skills
against the discussion's rationale. Prefer a deployment constraint, rejected design
tradeoff, or cross-component obligation that the snapshot does not already explain.
Do not remove documentation, loosen admission, or ask the agent to create nodes to
force the desired result. A follow-up comparison should use only actual reviewed
capture and permit the no-knowledge agent to succeed.

See the [protocol](../basic-memory-evaluation.md) and
[machine-readable evidence](basic-memory-astra-20260927.json). Full source snapshots,
actor edits, private regression, and native trace remain locally under
`.demo/basic-memory-20260927/`. Raw upstream material and traces are not published.
