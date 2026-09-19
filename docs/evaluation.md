# Behavioral evaluation protocol (not yet executed)

The demo and tests use hand-authored synthetic knowledge. They demonstrate mechanics,
not autonomous extraction accuracy, semantic search quality or productivity gains.

Before adoption, choose real tasks and record model/version, embedding model/revision,
task prompts, starting commits, budgets, repeat count, and reviewer rubric. Proposed
initial thresholds to approve before runs: no extra hidden-constraint violations,
at least 20% less repeated investigation, at least 90% supported/actionable accepted
nodes, and median maintenance under five minutes per accepted node. These are
experiment defaults, not achieved outcomes or agreed company policy.

For each task family:

1. Task A discovers a nontrivial constraint through investigation or a standardized
   human correction. Capture raw proposals separately from reviewer corrections.
2. Task C runs in a fresh agent conversation and isolated code checkout. Its prompt
   does not reveal the hidden constraint. Compare no knowledge, flat retrieval and
   graph expansion with equivalent entry retrieval and context budgets.
3. Change the relevant condition or scope and rerun maintenance and Task C. Score
   whether stale advice is avoided without treating a rename as invalidation.

Run the evaluator outside the tested agent's filesystem and credentials, for example
in a separate container with only the task repository and allowed knowledge mounted.
Do not put hidden tests or expected answers in a sibling directory visible to the
agent. Repeat across multiple tasks and fresh sessions; randomize control ordering.

Record correctness, hidden-constraint violations, retrieval timing, repeated
investigation, tool calls, time, tokens when available, human corrections, proposed
and accepted useful/unsupported/duplicate nodes, reviewer effort and stale-advice
errors. Keep automatic extraction results distinct from hand-corrected retrieval
fixtures. No adoption conclusion is justified by the bundled demo alone.
