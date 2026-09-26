---
name: knowledge-retrieve
description: Find existing project knowledge relevant to a coding task, question or broad topic using knowledge-agent search, code anchors and graph connections. Use before a design decision or when new questions arise during work. Return applicable findings without capturing or submitting knowledge.
---

# Retrieval workflow

Start with the user's task, question or topic. No candidate claim or proposed node
is required. Follow steps 1–6 and finish with findings for the calling task.
This workflow does not create/update nodes, write manifests, run task-end/propose,
review/accept proposals, or push knowledge. Synchronization may refresh the local
accepted checkout and derived index; it does not author knowledge.

## 1. Open the configured knowledge store

Use the installed CLI and the same configuration throughout. `CONFIG` means the
supplied config path; omit `--config CONFIG` for the environment/default configuration.
Read the configured repository map when code repository identities are needed.

```text
knowledge-agent --config CONFIG synchronize
```

Record the returned revision as `SHA`, embedding backend and stale warning. If
synchronization fails, inspect `status`: use `indexed_revision` only if a usable
index exists and disclose its stale state. If no index is usable, report the
blocker and stop. Do not initialize a new store as part of retrieval.

## 2. Frame the information need

Identify the task's goal, subsystem, known repository/files and open decisions.
Form queries from that context, without assuming a particular answer or node ID.
For example, start with "recovery export deployment compatibility" when changing
recovery delivery. If only a broad topic is known, begin with it and refine from
the results. Choose a bounded search effort appropriate to the task.

## 3. Find entry nodes

```text
knowledge-agent --config CONFIG search "TASK OR TOPIC" --repo REPO --revision SHA
knowledge-agent --config CONFIG lookup-anchor REPO RELATIVE_PATH --revision SHA
```

Use anchor lookup when a relevant code path is known; otherwise search is enough.
Omit `--repo` when identity is unknown or cross-repository knowledge may matter.
Default results are active nodes. Use `--all-statuses` deliberately when investigating
missing guidance or history; do not treat historical results as current advice.
In lexical mode, try alternative terms and anchors; paraphrase matching is unreliable.
If matches are weak, refine with a different task aspect or broaden repository scope.
If no useful entry is found within the search budget, proceed to step 6 with that gap.

## 4. Read and expand promising matches

```text
knowledge-agent --config CONFIG read NODE_ID --revision SHA
knowledge-agent --config CONFIG context NODE_ID --depth 2 --max-nodes 12 --max-tokens 12000 --revision SHA
```

Read plausible matches fully. Expand connections when they may expose constraints,
affected components or missing context. Connections are followed in both directions
by default; a `related_nodes` link does not establish dependency or truth.
Check truncation. Read an omitted relevant node directly or adjust the bounds if
the task warrants it; disclose remaining gaps. Do not expand the whole graph by habit.
New terms may justify another search/read/expand pass within the chosen budget.
Keep all results pinned to `SHA`; if the index changes, synchronize and repeat the
relevant retrieval against the new revision before combining findings.

## 5. Decide what applies

Compare each finding's scope, conditions, versions, evidence and status with the
current task and code. Distinguish verified facts, reports and inferences. Preserve
needs-review warnings; archived or superseded nodes are history. Conflicting or
missing evidence is a gap, not permission to invent a conclusion or repair the store.
Select only findings that inform the task's decisions, implementation or checks.

## 6. Return findings and end retrieval

Return the relevant node IDs and knowledge revision, actionable implications with
their evidence/conditions, and unresolved conflicts, stale state or search limits.
If nothing useful was found, say so without claiming that no knowledge exists.
Stop this skill here and return to the coding task. Do not continue into capture,
create a manifest (even an empty one), or submit any knowledge changes. Later
capture requires a separate knowledge-extract invocation under its own trigger.
