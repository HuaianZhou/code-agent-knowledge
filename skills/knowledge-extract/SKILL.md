---
name: knowledge-extract
description: Capture actionable project knowledge from the current coding-agent conversation and prepare Git proposals with knowledge-agent. Use at task completion, after an important correction or discovery, or before compaction; also retrieve existing knowledge when invoked at task start.
---

# Capture workflow

Execute these steps while conversation and working evidence are available. Deliver
either an explicit no-change result or a committed proposal with submission status.
You make semantic decisions; the CLI validates and stores the result.

## 1. Open the knowledge store

Locate the installed CLI and use the same configuration throughout. `CONFIG` below
means the supplied config path; omit `--config CONFIG` to use
`KNOWLEDGE_AGENT_CONFIG` or the default. Read the config to locate the knowledge
repository and provider.

Run `git -C KNOWLEDGE_REPO remote` to determine whether an `origin` is configured;
use the repository path from the configuration, not the coding project's repository.

```text
knowledge-agent --config CONFIG synchronize
```

Record the returned `revision` as `SHA`, embedding backend and stale warning.
If sync fails but `status` shows a usable index, use its `indexed_revision` and
report stale state. If neither is usable, report the setup error; do not claim
capture succeeded. Run `setup` only when installation/setup is in scope.

**Task-start invocation:** execute the searches, reads and graph expansion in step
3 for the upcoming task, check applicability, then stop. Capture runs at task end.

## 2. Extract and screen candidates

Review the current conversation, human corrections, experiments, failed approaches
and validated discoveries. For each candidate, identify its applicable condition,
conclusion, concrete future action, actual evidence, uncertainty and invalidation
conditions. Do not require an intermediate conversation-summary file.

Reject it if the complete conclusion is cheaply recoverable, fully covered by an
applicable skill, lacks a concrete action implication, or lacks plausible reuse.
Inspect applicable skills before declaring no overlap; scoped exceptions may
qualify and should reference the skill. Reject task summaries and temporary details.

**No survivors:** go to step 5 with an empty manifest. Retain rejection reasons for
the final report. Never create a node to meet a quota.

## 3. Search and read existing knowledge

For each survivor, search using its conclusion/action and then its underlying
condition. Substitute actual queries, repository identity and paths:

```text
knowledge-agent --config CONFIG search "QUERY" --repo REPO --all-statuses --revision SHA
knowledge-agent --config CONFIG lookup-anchor REPO RELATIVE_PATH --all-statuses --revision SHA
knowledge-agent --config CONFIG read NODE_ID --revision SHA
knowledge-agent --config CONFIG context NODE_ID --all-statuses --depth 2 --max-nodes 12 --max-tokens 12000 --revision SHA
```

Use anchor lookup for known code. Read full plausible matches and expand relevant
connections to find shared constraints. Use `related_nodes` for new links and
explain their relevance in the body; default graph traversal works in both directions. Broaden a scoped search without `--repo`
when needed. In lexical mode try alternative terms and anchors; it does not reliably
match paraphrases. Inspect truncation before claiming complete search coverage.

Compare subject, conclusion, conditions, versions, evidence and action implication.
Different titles do not prove novelty. Similar wording does not prove equivalence.
Treat archived/superseded nodes as history and retain needs-review warnings. Record
queries and compared IDs for admission. If the revision changes, synchronize and
repeat comparison against the new snapshot instead of mixing revisions.

## 4. Choose an operation

| Finding | Next action |
|---|---|
| Same scoped claim, nothing useful to add | No-op; reuse its ID if another candidate needs the constraint. |
| Same claim, additional evidence or corrected scope | Read it, preserve the stable ID, and prepare `update`. Retain relevant sources and relationships. |
| ID redirects | Read the survivor and use its ID; never recreate the retired ID. |
| No equivalent claim after comparison | Choose a new stable ID and prepare `create`; link shared constraints instead of copying them. |
| Conflicting evidence | Preserve both sources and uncertainty. Propose a scoped `needs_review` change or report an unresolved candidate; do not silently mark your conclusion verified. |

Run `read` for the intended ID before writing. A missing update target requires
resolving the intended ID, not changing the operation to create. For a new ID, only
a missing-node result establishes absence; a configuration/index error does not.
The proposal command checks existence again. ID checks do not replace comparison.

## 5. Write candidate files and manifest

Read [the node and manifest format](references/node-format.md). In a task-specific
scratch directory outside the accepted knowledge checkout, write complete Markdown
node files and one JSON manifest. Resolve node paths relative to the manifest.
Never edit the accepted checkout to capture knowledge.

Provide one `operations` entry and one admission declaration per supplied node.
Use actual gate rationales and the queries/IDs compared in step 3. Explain situation,
conclusion, action, rationale/evidence and invalidation in each body. Distinguish
reported, inferred and verified evidence. Do not fabricate anchors, revisions or
test results; a code commit does not establish deployment.

If all candidates were rejected or no-ops, write:

```json
{"nodes": [], "admission": []}
```

For each nonempty candidate file, execute and fix schema errors:

```text
knowledge-agent --config CONFIG validate --file CANDIDATE_FILE
```

Single-file validation does not check graph links; the next step validates the
complete resulting snapshot, including relationships among proposed nodes.

## 6. Create a proposal and check its result

```text
knowledge-agent --config CONFIG task-end MANIFEST_FILE
```

| Result | Next action |
|---|---|
| `zero_qualifying_candidates` | Report no knowledge changes with rejection/no-op reasons. No branch is created. |
| Validation error | Fix the specific candidate/operation/link and retry. Never turn a failed update into create just to bypass the error. |
| `committed: false` | Preserve the returned worktree, report the commit error, and finish the commit there after correcting its cause. Do not create duplicate proposal worktrees. |
| `committed: true` | Record branch, worktree and base revision; continue to step 7. This is proposed, not accepted knowledge. |

## 7. Route for review and submission

```text
knowledge-agent --config CONFIG review BRANCH
```

Compare duplicate candidates and scopes. If conflicts, integrity errors or stale
state block review, leave the branch pending and report the required correction.
A clean report still requires semantic maintenance review.

**No origin:** report the local branch and review revisions for explicit acceptance.
Capture does not self-approve knowledge. The reviewer may use `accept` after checking
admission, evidence and overlap. No GitHub repository, push or PR is needed.

**Origin configured and submission authorized:** write a review body explaining
claims, evidence, scope, comparisons and unresolved issues, then execute:

```text
knowledge-agent --config CONFIG push BRANCH
knowledge-agent --config CONFIG open-request BRANCH --title "Knowledge proposal: TOPIC" --body-file REVIEW_BODY_FILE
```

Open the request only after push succeeds and a supported provider is configured.
Use existing standing authorization; do not ask again for an already-authorized
submission. Without authorization/configuration, report the missing requirement
and keep the proposal local. If push succeeds but request creation fails, report
the pushed branch and request error. Reuse that branch when retrying.

## 8. Report the achieved state

Report the compared revision; rejected/no-op candidates or proposed IDs with their
operations; and the achieved state: no changes, pending commit, pending local review,
pushed branch or opened request. Include branch/worktree or request URL, evidence
and stale-state warnings, and the next concrete action. Never claim acceptance or
availability to other users before review, merge and their synchronization.

The host must invoke this workflow while task context remains available. Installing
the skill alone does not schedule capture.
