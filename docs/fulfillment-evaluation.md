# Fulfillment lifecycle pilot

This second synthetic fixture distinguishes implementation support from an
external consumer's deployed contract. It is a feasibility pilot, not a benchmark
of real-project productivity. The fixture source is in
`evaluation/projects/fulfillment`; the private consumer grader is
`evaluation/fulfillment_grader.py`.

The [completed Astra results](results/fulfillment-astra-20260924.md) include actual
captured nodes, review/acceptance records and all coding comparisons.

## Frozen protocol

1. Calibrate the grader against two evaluator-written implementations. Both pass
   public tests; only the implementation matching the external contract passes
   the consumer tests. Reverse the contract and verify the outcomes reverse.
2. Astra performs a streaming refactor, then invokes the capture skill on two
   synthetic operations handoffs. The store begins empty. A separate evaluator
   reviews raw proposals; do not silently edit them before reuse. Record exact
   accepted revisions and reasons. A failed capture is an outcome, not permission
   to inject curated replacement nodes.
3. Run export, recovery, and inventory tasks under no knowledge, semantic retrieval,
   and semantic retrieval with graph expansion: nine fresh sessions, one per cell,
   randomized order with seed 42. Same code, model, image, requested output budget,
   600-second wall limit and 6,000-byte node context limit. Actual usage comes from
   native traces; the output-token request is not a hard adapter limit.
   Follow-up tasks reset to the frozen source baseline; knowledge is carried
   forward, not the initial task's streaming refactor.
4. Report retrieved IDs, paths and truncation before interpreting any graph benefit.
   Flat search ranks the complete captured corpus; it is not artificially restricted
   to one entry node. Graph traversal uses the same top-ranked entry, depth two and
   the same byte limit. If capture creates no edges or both contexts contain the
   same relevant evidence, report the graph comparison as non-distinguishing.
5. Change the external receiver contract, run the maintenance skill on the accepted
   corpus, and review its actual correction proposals. Run export and recovery
   tasks against stale and maintained graph contexts, four additional fresh sessions.
   Keep starting code and task wording identical; only supplied knowledge differs.

Each preparation stores hashes of fixture, grader and protocol code before actor
execution. Tasks and checks must not be tuned after observing actor outcomes.
Infrastructure failures retain traces and may be retried in fresh directories;
behavioral failures remain in the report. Coding trials get no operations handoff
or private grader. The grader gets no credentials or network access. Source and
hidden graders are published for reproducibility but absent from actor mounts.

## What each result means

The north receiver initially accepts only CSV v1; south and new sites accept JSONL
v2. Code exposes both codecs but not that site assignment. Normal and recovery
exports feed the same receiver. After a reported migration, north accepts only
JSONL v2. The receiver checks parse actual output independently of editable codecs.

No-knowledge failures can be information deficits, not reasoning failures. Agents
may reasonably flag missing deployment information; record that behavior separately
from whether their code passes the external consumer checks. Inventory is a control
whose answer is in code. Knowledge-induced regressions and extra costs count against
the tool. The case where flat retrieval and graph perform equally is valid.

The initial handoff explicitly describes the shared obligation and invites supported
relationships. This tests execution with explicit capture guidance, not spontaneous
discovery of implicit graph structure. The evaluator reviews with Codex, not a blind
human. Retrieval is injected, so autonomous retrieval triggering remains untested.

## Reproduction

Use the existing Docker image and authentication setup in [evaluation.md](evaluation.md).
The model is Astra and MiniLM uses the same pinned revision as the earlier pilot.

```powershell
python -m unittest discover -s tests -p test_fulfillment_evaluation.py
python -m evaluation.fulfillment capture .demo/fulfillment-capture
python -m evaluation run .demo/fulfillment-capture/capture --image knowledge-eval-codex:local --network bridge --env-file .demo/codex-evaluation.env --codex-auth PATH_TO_AUTH_JSON
```

After separately reviewing and accepting the actual capture using the standard
`review` and `accept` workflow, pass its knowledge repo as `--source` to
`python -m evaluation.fulfillment reuse OUTPUT --source REPO`.
Run each trial in `experiment.json` through `evaluation run`, then `--grade`.
Alternatively, `python -m evaluation.fulfillment_run DIRECTORY --image IMAGE
--env-file ENV_FILE --codex-auth AUTH_FILE` runs that batch sequentially, stopping
on actor execution errors while retaining and continuing past behavioral failures.
Use `maintain OUTPUT --source REPO` for the external-condition maintenance trial.
The maintenance checkout must contain the original captured code commits so anchor
checks resolve. Import the capture project's history with `git fetch --no-tags
PATH_TO_CAPTURE_PROJECT main` from the maintenance project checkout; this adds
commit objects without changing its working files. Record that preparation step.
Use `reuse OUTPUT --source REPO --era after` for each of stale and maintained
corpora. All trial directories must be fresh.

`python -m evaluation.fulfillment_report ROOT [ROOT ...] --output REPORT.json`
collects execution records, independent grades, actual code diffs, native usage,
retrieved context and any `reviewer.json` scorecards. It does not turn an agent's
success claim into a pass.
