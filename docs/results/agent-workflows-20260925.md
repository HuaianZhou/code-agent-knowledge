# Standing capture and on-demand retrieval, 2026-09-25

Five completed isolated Astra sessions exercised two independent workflows. Every
coding task passed its separate private behavior grader. These are small synthetic
pilots, not a reliability benchmark or a real-project productivity measurement.

## Task-end capture

Both tasks used the same standing project AGENTS.md policy. Neither task request
mentioned capture, a skill path or a CLI command. The agent read the actual skill
and executed the task-end workflow in both sessions.

| Task | Observed result |
| --- | --- |
| Streaming refactor with Operations F-17/F-18 conversation | Proposed one reported constraint covering north CSV compatibility and both export paths, with sources and invalidation conditions. |
| Self-contained inventory fix | Submitted an empty manifest; zero writes and no proposal branch. |

The qualifying proposal remains a local proposal; accepted main stayed unchanged.
Its one-node organization differs from the earlier three-node capture but retains
the required meaning. Node count and exact wording were not prescribed.
Standing guidance worked here; it is not a guaranteed completion callback and has
not been installed in the user's global configuration.

[Capture evidence and reviews](task-end-trigger-20260925.json) include native
commands, proposed artifacts, execution metadata and separate coding grades.

## On-demand retrieval

Fresh sessions received ordinary coding requests and a generic standing retrieval
policy. They had access to the previously accepted three-node corpus from revision
`382f370abb14042ede4539f53e31619abb508eac`, not the new pending capture proposal.
No selected nodes, node IDs, operations conversation or suggested queries were
injected into these requests.

| Task | Agent behavior before implementation | Independent grade |
| --- | --- | --- |
| Normal export | Chose semantic search and anchor lookup, read receiver evidence and graph context, retained north CSV while using JSONL elsewhere. | Pass |
| Recovery export | Chose semantic search and anchor lookup, read graph context and recovery evidence, preserved north compatibility and reconstruction semantics. | Pass |
| Inventory control | Inspected code, skipped knowledge retrieval, fixed repeated-SKU summation. | Pass |

For normal export, retrieval completed at native events 20–27 before the first edit
at event 30. Graph context reported token truncation; a subsequent direct read
retrieved the recovery decision. For recovery, retrieval completed at events
16–23 before the first edit at event 26. Event indexes are zero-based JSONL indexes.
Actual retrieved text, code diffs and private consumer results support these
findings, rather than relying on final agent claims. All knowledge repositories
remained clean and unchanged, with no proposal branches.

The original export attempt hit the usage limit and was not behaviorally graded.
After reset, export and the unstarted inventory task ran in fresh workspaces with
identical requests and starting code. The interrupted attempt is retained as
invalid execution, and the unused original inventory preparation is distinguished
from a completed run in the [retrieval evidence](on-demand-retrieval-20260925.json).

## Interpretation and limits

The tool now has observed examples of capture from conversation under standing
instructions and retrieval chosen by the agent when needed. This supports its
usefulness for retaining operational constraints absent from code. The agent and
skill still make admission and application judgments; storage alone does not.

This does not establish an additional benefit from graph expansion over semantic
search: both export sessions also received relevant evidence through search and
anchor lookup. Context budgets and number of reads were agent-selected, so this
is not an equal-cost comparison with earlier injected-context experiments. Reviews
were performed by the parent Codex evaluator, not a blind human panel. Larger,
real-project trials and repeated executions remain needed.

Runtime: gpt-6-astra, Codex CLI 0.155.0-alpha.16, scoped Docker mounts and a separate
network-disabled grader. The immutable image and source hashes are in the JSON
reports. The two new preparation tests passed independently; the previously
reported 48-test suite was not rerun for this documentation/workflow addition.

See [capture setup](../task-end-capture.md) and
[retrieval setup](../on-demand-retrieval.md) for reproduction and opt-in policies.
