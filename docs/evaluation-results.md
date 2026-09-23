# Agent evaluation results

These are actual isolated Codex runs, not simulated adapter outputs. The project
and conversations are synthetic. They validate a small pilot, not real-project
productivity or adoption.

## Capture and maintenance

All eight scenarios passed artifact checks and a separate evaluator's review of
the native tool trace and resulting nodes. The evaluator is Codex from the same
model family, not a blind human reviewer. Model: `gpt-6-astra`; CLI:
`0.155.0-alpha.16`; embeddings: MiniLM revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

| Scenario | Observed result |
|---|---|
| Cheap lookup | Read the function definition; rejected the signature fact; executed zero-write submission. |
| Existing skill overlap | Read the supplied verification skill; rejected its duplicate instruction; zero writes. |
| Implicit constraint | Semantically searched the empty store; proposed one reported deployment/retention constraint. |
| Paraphrase | Searched, read and expanded the existing node; recognized equivalent meaning; zero writes. |
| Uncertain inference | Proposed a scoped verification rule with inferred evidence and needs-review status. |
| Zero value | Rejected a typo-only task as non-reusable; executed zero-write submission. |
| Shared constraint | Proposed an export decision with `constrained_by` pointing to the existing constraint. |
| Changed conditions | Archived the historical numeric constraint; revised two dependent nodes; preserved history and reported deployment uncertainty. |

The [full capture report](results/capture-astra-20260922.json) includes proposed
nodes, rubric judgments, actual command counts, native usage, image IDs and trace
hashes. All writes are proposals; accepted main was preserved.

Three cases completed before an Astra usage limit. After the user reset usage,
five ran in fresh workspaces. The [original blocked attempts](results/capture-agent-20260922.json)
remain recorded. A Sol probe/interrupted run is excluded at the user's request.
Retry preparation fixed an absent empty skills directory and cross-platform Git
line-ending noise without changing substantive scenario code or expectations.

## Semantic retrieval

Actual MiniLM inference and SQLite cosine comparisons returned the target at rank 1
for all ten paraphrased queries: Recall@3 = 1.0, MRR@3 = 1.0. See the
[retrieval report](results/semantic-minilm-20260922.json). This small corpus is a
smoke test; it is not a broad search-quality benchmark.

## Coding reuse comparison, 2026-09-23

All nine Astra executions completed and passed the separate, network-disabled
behavioral grader. Each used a fresh workspace and session, identical starting
code, the same Docker image, and the same requested budget.

| Condition | Passed | Median wall time |
|---|---:|---:|
| No knowledge | 3/3 | 77.8 seconds |
| Semantic retrieval without graph expansion | 3/3 | 81.7 seconds |
| Semantic retrieval with graph expansion | 3/3 | 81.9 seconds |

The hidden checks verify preserved numeric meanings, replay of historical records,
and the new REFUNDED round trip. The [full reuse report](results/reuse-astra-20260923.json)
records actual code diffs, starting hashes, grader and trace hashes, native token
usage, and execution metadata. One trial completed before a usage limit; the
remaining eight ran after reset, retaining the successful original trial.

This result demonstrates neither a knowledge-base benefit nor an additional graph
benefit on this task. It does not establish that either is unhelpful. Existing code
already exposes the numeric compatibility requirement, so the baseline can solve
the problem. Flat retrieval also includes the key constraint B. Graph expansion
includes A and B within the context budget but omits C. Thus this fixture cannot
show the proposed advantage of reaching C through B. Three repetitions and these
timings do not support a productivity conclusion. Retrieval was supplied to the
agent; autonomous retrieval invocation was not measured.

### Next experiment needed to distinguish the benefits

Use a constraint established by real operational evidence that is absent from
the checked-in implementation, such as a supported external reader's deployment
contract. Freeze the task, evidence, grading criteria, and retrieval parameters
before running agents. Do not change them in response to which condition wins.

Compare no knowledge with semantic retrieval to measure the knowledge base's
contribution. Compare that same semantic retrieval with graph expansion to measure
the graph's additional contribution. First record the actual retrieved node IDs,
paths, and truncation: if both conditions deliver the same relevant evidence, the
trial cannot distinguish graph expansion. Include tasks where semantic search
alone should suffice as controls; do not deliberately cripple flat retrieval.

For a graph-sensitive task, use the A-to-B-to-C path to expose a separately affected
component or verification obligation, then grade the resulting implementation and
compatibility tests. A controlled path-only test may establish that the mechanism
works, but claims of practical value require naturally occurring retrieval gaps
and a real project. These follow-up experiments have not yet been run.
