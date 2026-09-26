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
If only a focused topic is known, begin with it and refine from results. A detailed
question may have no obvious tag; do not force one. Choose a bounded search effort
appropriate to the task and identify what information would resolve its decisions.

## 3. Find entry nodes

Choose an entry route from the information available:

- **Useful metadata is known or reasonably suggested:** try an exact tag/type
  filter. Prefer tags observed in results, project guidance or the request; a guessed
  label is only a hypothesis. Type alone describes the kind of knowledge, not its topic.
  Metadata browsing can use `search --order weight --tag TAG --repo REPO --revision SHA`;
  optionally add `--type TYPE`. Weight is importance, not relevance or completeness.
- **No confident metadata match, or a detailed question:** search content directly
  with `search "TASK OR QUESTION" --repo REPO --revision SHA`, without tag/type filters.
  With the semantic backend, this searches embeddings of title, type, tags and the
  full body together; it is not gated on title similarity or a separate passage index.
- **A source file or symbol is known:** use `lookup-anchor REPO RELATIVE_PATH
  --revision SHA` (optionally `--symbol SYMBOL`) as another entry point. If anchors
  are absent or insufficient, use content search; an unanchored node may still matter.

Prefix these commands with `knowledge-agent --config CONFIG`. Tag/type filters are
exact restrictions, not fuzzy metadata matching. Inspect whether results address
the task's decisions: a nonempty list of topical but unhelpful nodes is insufficient.
For empty or insufficient metadata results, remove uncertain tag/type restrictions
and search the question semantically. Do not retain a failed filter on the fallback
query. Even useful filtered results may leave a decision requiring broader search.
Use discovered terms for follow-up queries rather than repeatedly guessing tags.

Omit `--repo` when identity is unknown or cross-repository knowledge may matter.
Default results are active nodes. Use `--all-statuses` deliberately when investigating
missing guidance or history; do not treat historical results as current advice.
The configured backend determines content search: the CLI does not automatically
switch between semantic and lexical modes. In lexical mode, try alternative terms
and anchors, disclose that limitation, and do not claim semantic retrieval occurred.
If content matches are weak, refine with a different task aspect or broaden scope.
If no useful entry is found within the search budget, proceed to step 6 with that gap.

## 4. Read and expand promising matches

```text
knowledge-agent --config CONFIG read NODE_ID --revision SHA
knowledge-agent --config CONFIG context NODE_ID --depth 2 --max-nodes 12 --max-tokens 12000 --revision SHA
```

Read plausible matches fully. Inspect a bounded set of connected neighbors from
useful entry nodes, including neighbors whose titles seem weakly related to the
original query. Judge their content by whether it changes a decision, constraint
or verification need. Expand further for new obligations or unresolved questions;
stop when resolved, further exploration adds nothing actionable, or the budget ends.
Connections are followed in both directions
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
