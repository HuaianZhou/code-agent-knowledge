# Validation record

Local validation on Windows, Python 3.12, Git 2.53, PyYAML 6.0.3 and sqlite-vec 0.1.9:

- Editable package build/install and CLI entry point work.
- Integration tests exercise real temporary Git repositories and sqlite-vec, not
  mocked repository/index operations.
- Complete local demo passed: isolated proposal → review → explicit fixture
  acceptance → bare-remote sync → separate reader → A → B ← C → rename impact.
- Zero-candidate demo produces zero writes. Both skill frontmatters validated.
- Failure injection demonstrated index rollback; simultaneous writers produced
  coherent snapshots. Offline-sync regression retains the last accepted revision.

Not executed: an approved transformer model download/inference, hosted GitHub/GitLab
requests, scheduled agent execution, autonomous extraction, or controlled fresh-agent
behavioral evaluation. These results establish local mechanics, not adoption value.

Local setup and acceptance coverage: new repository/config/index creation, repeatable
setup, preservation of existing directories, no-remote synchronization, explicit
reviewed-commit acceptance and index refresh, stale/concurrent review rejection,
dirty-checkout preservation, acceptance locking and remote-workflow separation.
All 33 automated tests passed after this change. The Windows `install.ps1` script
built and installed the wheel, created a separate demo knowledge repository and
index, and the installed CLI was checked from outside the source root.

The capture and maintenance skills were refactored into executable workflows.
Both passed skill validation. Their command sequences were exercised on local,
hand-authored fixtures: zero-write capture, schema validation, create/update proposals,
review, local acceptance, retrieval, anchor lookup, maintenance and impact inspection.
This checks command compatibility, not autonomous agent judgment or capture quality.

## Three-layer evaluation implementation

On 2026-09-21, all 44 automated tests passed (69 seconds). Added tests cover
cross-repository anchor isolation, combined filters and ordering, incremental/full
index equivalence, local/remote proposal visibility, evaluator isolation boundaries,
artifact-based scoring, and hidden-grader calibration against compatible and broken
fixture implementations.

The evaluation CLI prepared eight capture/maintenance scenarios and nine reuse
trials (three conditions, three repeats). These are explicitly `prepared_not_run`,
with model `not-configured`; preparing fixtures is not an agent evaluation.
The offline lexical diagnostic returned Recall@3 = 0.9 and MRR@3 = 0.7333 over ten
queries. Its `passed` field is null: this does not establish semantic retrieval.

Docker and the optional embedding backend are unavailable in this environment.
Real isolated agent runs, independent capture scorecards, transformer inference,
and real-project adoption measurements remain pending. See [the executable
evaluation guide](evaluation.md) and [coverage map](evaluation-coverage.md).

## Semantic retrieval run, 2026-09-22

Installed Sentence Transformers 5.7.0 and Torch 2.14.0 in the project environment.
Ran actual model inference and SQLite cosine search with
`sentence-transformers/all-MiniLM-L6-v2` pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (384 dimensions).
All ten queries returned their target at rank 1: Recall@3 = 1.0, MRR@3 = 1.0,
passing the predeclared 0.8 Recall@3 threshold. The full
[machine-readable result](results/semantic-minilm-20260922.json) records every query.
This is a small synthetic retrieval test, not an agent-capture evaluation.

All 46 automated tool/harness checks passed. The two new checks verify semantic
setup configuration preservation and mandatory explicit embedding selection in
capture preparation. Fresh eight-case capture and nine-trial reuse suites use
the same pinned semantic model. They remain prepared, not agent-executed.

## Actual capture/maintenance agent runs, 2026-09-22

Executed all eight scenarios using Codex CLI `0.155.0-alpha.16`, model alias
`gpt-6-astra`, and the pinned MiniLM embedding model in isolated Docker containers.
All eight passed artifact checks and a separate Codex evaluator's trace/node review.
This is not a blind human review or evidence of real-project adoption. The
[results and per-criterion reviews](results/capture-astra-20260922.json) include
actual proposed nodes, native token usage, command counts, image IDs and trace hashes.

Observed outcomes: cheap lookup, skill overlap, paraphrase and zero-value tasks
produced zero writes. The implicit constraint produced a reported constraint;
uncertain inference produced an inferred, needs-review verification rule; the export
decision reused the existing constraint through an explicit edge. Maintenance archived
the historical numeric constraint and revised two dependent nodes while retaining
their history and distinguishing reported deployment evidence from the observed test.
All contributions remain proposals; none was accepted into main.

The initial run completed three cases before the CLI reported a usage limit.
The [initial attempt record](results/capture-agent-20260922.json) retains those
quota-blocked attempts. After the user reset usage, the five remaining cases ran
in fresh workspaces. An alternative-model readiness check and interrupted Sol run
are excluded. Two fixture issues found during execution (empty skills directory and
Windows/Linux line-ending differences) were corrected for retry preparation without
changing scenario conversations, substantive code, or expected outcomes.

The seven harness regression tests passed after adding narrow read-only Codex
authentication mounting; the grader receives no authentication file. Docker images
cache the embedding model and use CPU Torch. Local raw traces and Git proposals are
retained under `.demo/capture-agent-20260922` and
`.demo/capture-astra-retry-20260922`.

## Actual coding reuse runs, 2026-09-23

All nine Astra trials completed: three without knowledge, three with semantic
retrieval, and three with semantic retrieval plus graph expansion. Each passed
the separate hidden grader for numeric compatibility, historical replay, and the
new REFUNDED round trip. One successful original trial was retained; eight fresh
trials completed after the usage reset, with matching starting file hashes and
context contents. Raw artifacts remain in `.demo/reuse-agent-20260922` and
`.demo/reuse-astra-retry-20260923`.

See the [machine-readable results](results/reuse-astra-20260923.json) and
[interpretation and next experiment](evaluation-results.md). Neither a knowledge
base benefit nor an additional graph benefit was demonstrated: the code makes the
compatibility requirement apparent, and flat retrieval already includes it.
This is an inconclusive small synthetic comparison, not evidence against either
approach. Real-project value and autonomous retrieval remain untested.

## Fulfillment lifecycle pilot, 2026-09-23–24

Forty-eight automated tests passed, including two new calibration tests covering
opposite consumer contracts and the inventory control. Correct and incorrect
deployment variants both pass public tests; the independent grader distinguishes
them and reverses acceptance after migration. Fixture/grader/protocol hashes were
frozen before actor execution and verified unchanged afterward.

Fifteen Astra sessions completed: actual streaming change plus capture, nine
controlled coding trials, maintenance triggered by an external report without a
source diff, and four stale/maintained coding trials. A quota-interrupted attempt
was preserved and retried in a fresh workspace after reset; no completed behavioral
failure was removed. All coding starts and consumer grader hashes matched.

Capture proposed three reported-evidence nodes with two constrained_by edges.
Maintenance revised all three IDs, kept history and reported evidence, and preserved
the dependency edges. Both were accepted unchanged after separate Codex review,
not blind human review. The source history was imported for the maintenance clone
to make captured anchors resolvable without altering its files; the anchor scan
was clean, and the external condition change still caused correction proposals.

No knowledge: 1/3 initial coding tasks passed. Semantic: 3/3. Semantic plus graph:
3/3. After migration, stale knowledge: 0/2; maintained: 2/2. These are separate
consumer grades, not self-reported success. The small synthetic fixture supports
knowledge-transfer and maintenance behavior, but flat/graph evidence overlap and
context truncation prevent a claim of additional graph benefit. See the
[full results](results/fulfillment-astra-20260924.md) and
[machine report](results/fulfillment-astra-20260924.json).

## Standing capture and on-demand retrieval, 2026-09-25

Two new preparation tests passed with `python -m unittest tests.test_task_end_trigger tests.test_on_demand -v`. Five isolated Astra sessions completed with separate passing coding grades. Standing capture proposed one qualifying constraint and correctly wrote nothing for the code-only control. On-demand export and recovery retrieved relevant evidence before edits; inventory skipped retrieval. All accepted stores remained unchanged. Frozen preparation/policy/grader hashes matched after execution. The usage-interrupted export attempt is retained separately; its fresh retry passed. See the [workflow report](results/agent-workflows-20260925.md) for evidence and limits.

## Generic graph connections, 2026-09-25

New links use `type: related_nodes` inside the existing `relations` list. Context traversal remains bidirectional by default. Impact review now traverses all connections in both directions, including legacy labels, and only suggests review; it does not change accepted status. This may expand candidate lists to the entire connected component. Existing accepted Markdown and historical agent reports remain unchanged.

`python -m unittest discover -s tests -v`: 52 tests passed. Coverage includes generic proposals/acceptance/merge redirects, traversal cycles and budgets, connected impact from either endpoint, disconnected-node exclusion, and compatibility with every legacy relationship label. Both updated skills passed the skill-creator validator; `git diff --check` passed. Historical agent experiments used the earlier relationship schema; they were not rerun for this change.

## Separate retrieval skill, 2026-09-26

`python -m unittest tests.test_on_demand tests.test_task_end_trigger -v`: both preparation tests passed. Both knowledge-retrieve and knowledge-extract passed skill validation. Three fresh Astra coding sessions passed independent consumer grades; export/recovery loaded the new retrieval skill, inventory skipped retrieval, and no capture/proposal commands or knowledge changes occurred. Frozen skill/policy/preparation/grader hashes matched. See the [report](results/retrieval-skill-split-20260926.md) for evidence and limits, including the supplied example query and absence of a fresh capture run.
