# On-demand knowledge retrieval

The fulfillment comparison supplied selected node records to coding agents. This
pilot instead exposes the existing CLI and the previously reviewed, accepted
three-node corpus. No node content, node IDs, operations conversation or suggested
queries appear in the coding request. There is no preselected `knowledge.json`.

The [standing retrieval policy](../integrations/codex/retrieval.fragment.md) tells
the agent that project knowledge is available, how to access it, and when it may
matter. It leaves query choice, reads and graph expansion to the agent. It permits
skipping retrieval for self-contained changes. This is configured tool use, not
discovery without any instruction about the tool's existence.

Run fresh sessions for normal export, recovery export and the unrelated inventory
fix. A separate, unchanged consumer grader checks the implementation. An evaluator
also checks native traces: retrieval must deliver relevant evidence before the
compatibility implementation, and the final code must use it correctly. Record
unnecessary retrieval on the control rather than counting any tool call as success.
The knowledge repository must remain unchanged: this pilot tests retrieval only.

## Reproduce

```text
python -m evaluation.on_demand OUTPUT --source ACCEPTED_KNOWLEDGE_REPO
python -m evaluation.fulfillment_run OUTPUT --image IMAGE --env-file ENV_FILE --codex-auth AUTH_FILE
python -m evaluation.on_demand_report OUTPUT --output REPORT.json
```

Use the Docker runtime from [evaluation.md](evaluation.md). The source is the actual
accepted capture from the fulfillment pilot, not the new task-end-trigger proposal,
which is deliberately still pending review/acceptance. Both pilots are independent.

Native traces, agent-selected query text, returned records, code diffs, independent
grades and separate evaluator reviews establish what occurred. CLI commands alone
do not prove semantic usefulness. This pilot has one run per task and permits
agent-selected context sizes and multiple reads; it is not an equal-cost comparison
with the earlier injected 6,000-byte contexts. It cannot isolate the extra benefit
of graph expansion over semantic retrieval.

For a real project, append the policy fragment to existing `AGENTS.md`, replacing
its config/skill/repository-map placeholders as described in
[task-end capture](task-end-capture.md). If combining retrieval and capture, replace
the retrieval fragment's final retrieval-only restriction with the task-end policy's
local-proposal authorization. Do not retain conflicting instructions. No global
configuration is changed by these evaluation commands.

## Observed pilot results

The [2026-09-25 workflow report](results/agent-workflows-20260925.md) records
completed Astra runs, native evidence, independent grades and limitations.
