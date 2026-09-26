# Evaluating retrieval entry routes

The retrieval skill allows exact metadata browsing when a useful tag/type is known,
unfiltered content search when it is not, and anchor lookup for known source code.
Empty **or insufficient** filtered results require broader search. Inspect connected
content even when its title looks unrelated; remain within a declared search budget.
Semantic versus lexical search is configured, not an automatic backend fallback.

## Frozen scenarios

`evaluation/retrieval_routes.py` defines a seven-node reported-evidence corpus and
eight focused questions. Expected IDs and reasoning stay in private evaluator data;
the agent can retrieve the actual corpus through the tool. Facts are synthetic.

| Case | Challenge | Required evidence or behavior |
| --- | --- | --- |
| metadata_hit | A supplied existing tag is useful. | Find stable stored values and independently deployed readers. |
| empty_metadata | Suggested `retries` tag does not exist. | If attempted, discard it on content search; reconcile charge outcome before resending. |
| weak_metadata | `retry` returns a timer rule, not the needed safety rule. | Recognize nonempty is insufficient; find partner non-idempotency outside that tag. |
| detailed_question | Lost bank response; no suggested tag or obvious title. | Find the detail in the Partner agreement body without requiring a guessed tag. |
| anchor_entry | Known writer.py path. | Locate the anchored entry and inspect connected archive and restoration obligations. |
| weak_title_neighbor | A lifecycle change has an unobvious verification obligation. | Read Continuity rehearsal and explain the restore check; record its discovery route. |
| wrong_type | User expects a decision; relevant record is a constraint. | Drop the uncertain type restriction and find tenant-aware cache keys. |
| no_evidence | Store contains no approved signature algorithm. | Do not interpret nearest neighbors as approval; report searched scope and missing evidence. |

## What automated tests establish

`python -m unittest tests.test_retrieval_routes -v` checks exact metadata inclusion/
exclusion, weak-match distractor construction, body inclusion in the embedding
payload, anchor isolation, the two-hop graph path, and isolated preparation without
answer/rubric injection. These tests use lexical indexing for offline mechanics.
They **do not** establish semantic ranking, agent fallback decisions or answer quality.

## Run actual agent evaluations

```text
python -m evaluation.retrieval_routes .demo/retrieval-routes-RUN
python -m evaluation run .demo/retrieval-routes-RUN/weak_metadata --image knowledge-eval-codex:local --network bridge --env-file .demo/codex-evaluation.env --codex-auth PATH_TO_AUTH_JSON
```

Run each directory named in experiment.json in a fresh session. The prepared
configuration uses the pinned semantic embedding model from the fulfillment pilot.
Use the existing Docker runtime from evaluation.md. This is an answer/retrieval
evaluation: do not use the fulfillment coding grader or interpret actor exit 0 as
a passing answer. No automatic semantic-answer grader is provided.

Before interpreting an agent run, calibrate the frozen corpus using a real embedding
model: issue representative detailed questions without tag/type restrictions and
record target rank/top-K recall, not exact floating-point scores. Record metadata
exclusions and graph paths independently. A target absent from semantic results is
a retrieval failure worth retaining, not a reason to silently rewrite the fixture.

## Review each completed run

Use the private criterion and native agent trace together. Record:

- Execution/model validity and whether the correct skill was read.
- Queries, exact filters, returned IDs, reads, graph paths and truncation.
- Whether metadata was attempted and whether broadening actually removed its filters.
- Relevant source text delivered before the answer, and whether the answer correctly
  applies it, preserves reported confidence and identifies unresolved gaps.
- Original versus final knowledge/code Git revisions, clean status and absence of
  proposals, manifests or write commands. Synchronization/index updates are allowed.
- Search/read count, context volume, native token usage, and limits encountered.

Mark each rubric item pass/fail/unresolved with trace evidence. A tool call or cited
ID alone is not a pass. An agent that correctly chooses semantic search immediately
may pass the answer criterion but leaves the metadata-fallback behavior **unexercised**;
do not count that as a successful fallback. Forced-route diagnostic runs must be
labelled separately from natural agent choice. Inspect insufficient-result cases
semantically; a nonempty result count cannot establish usefulness.

For graph discovery, distinguish information first delivered by search from information
first delivered through expansion. If both already contain the key fact, do not claim
additional graph benefit. The graph fixture establishes a supported path, not a
guaranteed ranking gap.

To compare policies, freeze the same corpus/questions/model/budgets and run the old
and updated skills in independent sessions, ideally with repeated runs. Compare
answer support, missed obligations and cost. Retain failures and quota interruptions.
Until those agent runs are completed, these are designed scenarios and tested
facilities, not evidence that the new policy improves agent performance.
