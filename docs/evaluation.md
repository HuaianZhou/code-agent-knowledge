# Three-layer evaluation

Run these commands from the tool's source repository using its Python environment.
`evaluation/` is evaluator tooling, not a production knowledge store or part of the
installed CLI package. Put outputs under `.demo/` (Git-ignored). Never publish raw
agent traces containing real project data without the project's sharing approval.

## 1. Tool behavior and retrieval

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use actual temporary Git repositories, SQLite and sqlite-vec. The
[coverage map](evaluation-coverage.md) links the proposed scenarios to tests and
distinguishes existing coverage, added coverage and evaluations not yet run.

Semantic retrieval has its own corpus: eight knowledge nodes and ten paraphrased
queries. It scores Recall@K and MRR@K using target IDs/ranks, never exact floating
scores. K must be smaller than the corpus. The pilot default is Recall@3 >= 0.8;
change the threshold before running, not after inspecting results.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[semantic]"
.\.venv\Scripts\python.exe -m evaluation retrieval --output .demo/semantic-run --model APPROVED_MODEL --revision FULL_IMMUTABLE_MODEL_COMMIT --k 3 --threshold 0.8
```

Select a Sentence Transformers model and its full 40-character revision. The model
may download on first use; document/query embeddings use the same space. Results
include payload policy, model revision, dimensions, knowledge commit and per-query
ranks. This small synthetic corpus is a smoke test, not production retrieval quality.

For an offline check of the harness, use `--lexical-diagnostic` instead of model and
revision. Its report deliberately has `kind: lexical_diagnostic` and `passed: null`.
It can never count as a semantic-search pass.

## 2. Capture and maintenance skill evaluation

Prepare fresh public inputs and private evaluator criteria:

```powershell
.\.venv\Scripts\python.exe -m evaluation prepare-capture --output .demo/capture-run --model PINNED_AGENT_MODEL
```

Eight fixed scenarios cover cheap lookup, existing-skill overlap, an actionable
human-reported constraint, paraphrase/reuse, uncertain inference, zero-value work,
reuse of a shared constraint, and maintenance after a genuine condition change.
Inputs include conversations, runnable project code, existing knowledge and relevant
skills. The maintenance case includes actual before/after code commits and a
reported deployment correction. Cases are synthetic, not company facts.

Each trial contains:

```text
trial/
  input/        Agent-visible request, skills and CLI source (read-only)
  workspace/    Independent writable code/knowledge repos and config
  output/       Raw results and traces written by the agent adapter
  private.json  Evaluator-only expectations, rubric and baseline revision
```

Run the actual agent only in a container with the restricted mounts below. A fresh
directory alone is not isolation. The runner never mounts private.json, evaluator
source, other trials, the Docker socket, or the host home. No host-run fallback
exists. `run` refuses to start without Docker, and each trial can run only once.

Build `evaluation/Dockerfile` as a base runtime, then derive an image that installs
your chosen coding-agent CLI. It includes Python, Git, YAML/sqlite-vec dependencies
and a generic adapter; **it does not include an LLM or coding-agent installation**.
The final image must be built/pulled explicitly; runs resolve and record its local
immutable image ID and never silently pull a new image.

The adapter accepts these environment variables via an evaluator-owned env file:

```text
EVAL_MODEL_ID=PINNED_AGENT_MODEL
EVAL_AGENT_COMMAND_JSON=["YOUR_AGENT_EXECUTABLE","FRESH_SESSION_FLAG","PROMPT_FLAG","{prompt}"]
```

Replace the example argv with your agent's real arguments. Configure that command
to start a new conversation, use the declared model/version and output-token budget,
and emit its native tool trace. The adapter uses argv directly, without a shell.
It gives the agent the request and obtains capture outcome from actual Git branches,
not a narrative assertion. Native model/tool/token metrics remain null until measured
from the agent's trace; do not interpret missing metrics as zero.

```powershell
.\.venv\Scripts\python.exe -m evaluation run .demo/capture-run/implicit_constraint --image YOUR_AGENT_IMAGE --env-file PATH_TO_ENV_FILE --timeout 600
```

Default network is `none`. A remote-model agent can explicitly use `--network bridge`
with its existing authentication supplied through the env file. The container has
no host filesystem access beyond its scoped mounts. This is filesystem isolation,
not a defense against a malicious agent attacking network-accessible services;
choose the network/model environment accordingly. Credentials are not written into
the request or experiment metadata. The image needs a fresh-session command that
can authenticate without a host-home mount.

Score actual artifacts, then perform independent semantic review:

```powershell
.\.venv\Scripts\python.exe -m evaluation score-capture .demo/capture-run/implicit_constraint
.\.venv\Scripts\python.exe -m evaluation score-capture .demo/capture-run/implicit_constraint --scorecard PATH_TO_COMPLETED_SCORECARD
```

Use [the scorecard template](../evaluation/scorecard.example.json), replacing every
example judgment with an independent review and references to artifacts/trace.
The scorer checks the actual branch, changed IDs, zero-write behavior, preservation
of accepted main, evidence-state constraints and relationship reuse. It does not
pretend code can decide semantic equivalence or all admission criteria.
Until reviewed, the result is `needs_semantic_review`; without a successful isolated
run it is `unverified_run`. Neither exits as a passing evaluation. Raw proposed
nodes are retained in the score report, separately from later corrections.

Inspect the trace for actual search/read/capture or maintenance commands. A plausible
proposal alone does not prove the skill followed the workflow. Score admission,
evidence, scope, reuse and relationship meaning, not exact wording.

## 3. Controlled task reuse: no knowledge / flat / graph

Prepare paired trials with identical starting code, model declaration, output-token
budget and knowledge context budget. Run order is randomized using a recorded seed.

```powershell
.\.venv\Scripts\python.exe -m evaluation prepare-reuse --output .demo/reuse-curated --model PINNED_AGENT_MODEL --repeats 3 --context-budget 2400 --seed 42
```

The default corpus is explicitly `curated_fixture`. To test the output from Task A
without silently hand-correcting it, prepare a separate experiment:

```powershell
.\.venv\Scripts\python.exe -m evaluation prepare-reuse --output .demo/reuse-raw --model PINNED_AGENT_MODEL --capture-trial .demo/capture-run/implicit_constraint --repeats 3
```

Raw experiments read the submitted proposal commit (or an empty set after zero
writes). They preserve that provenance and do not label it accepted knowledge.
Never combine raw and curated outcomes into a single extraction-quality metric.

All conditions receive the same task prompt to add REFUNDED support. The prompt
does not disclose the hidden historical compatibility requirement. Flat and graph
share exactly one entry search and the same corpus. Flat fills its context using
query ranking; graph expands the same entry through both directions. Both use the
same conservative UTF-8-byte budget for complete node records and expose usage and
truncation. They need not use exactly equal bytes due to indivisible records.

This is **controlled retrieval**, supplied in a read-only context file to isolate
graph expansion's contribution. It does not prove that an agent spontaneously
invokes retrieval before coding. That requires a subsequent host-integration study.
The pilot uses lexical entry retrieval consistently in both conditions; semantic
search is evaluated separately in layer 1. The no-knowledge agent receives no corpus
or search index, and none of the agents receives the private grader.

Execute each trial in `experiment.json`'s run order with the same image, network and
600-second timeout, then grade it in a separate network-disabled container after
the coding agent has exited:

```powershell
.\.venv\Scripts\python.exe -m evaluation run TRIAL_DIRECTORY --image YOUR_AGENT_IMAGE --env-file PATH_TO_ENV_FILE
.\.venv\Scripts\python.exe -m evaluation run TRIAL_DIRECTORY --image YOUR_AGENT_IMAGE --grade
.\.venv\Scripts\python.exe -m evaluation summarize-reuse .demo/reuse-curated
```

Only the grading container receives hidden tests. The tests check the requested
feature and compatibility of actual produced code. Agent claims such as “I used B”
do not count. The summary requires successful execution, matching declared model,
and passing grading; absent runs remain pending. Review raw traces independently
for use-before-decision, unnecessary investigation, incorrect edits, corrections
and context cost. Grader success alone does not establish causal use of knowledge.

## Completion criteria and limits

- Tool tests: all pass; remote proposal visibility is tested separately from acceptance.
- Semantic pilot: actual transformer backend meets the predeclared Recall@K threshold.
- Capture: scenario contract checks and all independent rubric dimensions pass.
- Reuse: all hidden checks pass; report per-condition failures and costs over repeats.
- Maintenance: changed-condition scenario revises the affected constraint without
  inventing verification, deleting history or blindly invalidating dependents.

For adoption, predeclare real-project targets and acceptable reviewer overhead.
Suggested discussion starting points are no extra constraint violations, 20% less
repeated investigation, 90% supported/actionable accepted nodes and median maintenance
under five minutes per accepted node. These are not achieved results or company policy.

The bundled project is intentionally small and synthetic. Repeated real-project tasks
and independent sessions are still required before claiming productivity improvement.
Plain-Git team acceptance remains manual/external: its transport test advances remote
main using Git and explicitly does not claim a tool-managed remote acceptance flow.
