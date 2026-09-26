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
its config/repository-map placeholders as described in
[task-end capture](task-end-capture.md). Set `SKILL_PATH` to the installed
`skills/knowledge-retrieve/SKILL.md`, not the capture skill. Retrieval has its own
steps 1-6 and ends with findings, without manifests or proposals. If combining retrieval and capture, replace
the retrieval fragment's final retrieval-only restriction with the task-end policy's
local-proposal authorization. Do not retain conflicting instructions. No global
configuration is changed by these evaluation commands.

## Observed pilot results

The [2026-09-25 workflow report](results/agent-workflows-20260925.md) records
completed Astra runs, native evidence, independent grades and limitations.

The original pilot above used the earlier combined capture/retrieval skill. New
preparations use the dedicated retrieval skill; historical results are unchanged.

## Updating an existing integration

Install/copy the new `skills/knowledge-retrieve` folder alongside the updated
`knowledge-extract` folder in your agent's skill directory. Change retrieval-only
AGENTS.md instructions from the old extraction skill path to the retrieval skill
path and remove instructions to jump to capture step 3. Keep task-end capture
instructions pointing to knowledge-extract. Start a fresh agent session so it
loads the updated instructions. This repository change does not modify global
skills or project AGENTS.md files automatically.

The separate flows are:

- Retrieval: open store → frame task/topic → find entry nodes → read/expand →
  assess applicability → return findings and stop.
- Capture: open store → screen conversation candidates → compare existing nodes →
  choose operation → prepare manifest → propose → route for review → report.

Capture still searches for duplicates; those searches do not turn it into a
retrieval-only workflow. A later capture invocation is separate from retrieval.

The [dedicated-skill validation](results/retrieval-skill-split-20260926.md) reran
three fresh Astra tasks after this split: both export tasks retrieved through the
new skill, inventory skipped retrieval, and all knowledge stores stayed unchanged.

## Metadata, content and anchor entry routes

The skill now treats known tag/type filters as an optional entry, uses content
search directly for detailed questions without confident metadata, and broadens
empty or insufficient filtered results. Source anchors provide another entry.
The [retrieval-route evaluation](retrieval-route-evaluation.md) defines eight
scenarios and separates mechanical checks from actual agent judgments.
