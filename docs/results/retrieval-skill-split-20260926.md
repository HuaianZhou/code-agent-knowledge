# Dedicated retrieval skill validation, 2026-09-26

Retrieval now has its own knowledge-retrieve skill with six sequential steps and
an explicit end without knowledge writes. Knowledge-extract no longer provides
a task-start shortcut; its searches compare capture candidates with existing nodes.
Integration policy and evaluation preparation now load the dedicated skill.

Three fresh Astra sessions completed using the previous accepted fulfillment
corpus and unchanged independent consumer grader. Each coding request provided
only the task, project path, model and budget. No selected node content or IDs
were injected. The skill itself contains a recovery-query example, and the recovery
agent used it; this is not a test of unaided query formulation.

| Task | Observed behavior | Private coding grade |
| --- | --- | --- |
| Recovery | Read knowledge-retrieve at event 6; retrieved at 13, 17 and 19; stated the north exception at 20 before editing at 22. | Pass |
| Normal export | Read knowledge-retrieve at event 6; chose its search, retrieved at 15, 17 and 19; stated the north exception at 20 before editing at 22. | Pass |
| Inventory | Inspected code and standing policy; skipped retrieval for the self-contained fix. | Pass |

Both export agents returned to coding after retrieval. They retained north CSV,
used JSONL elsewhere, and preserved the required explicit override/reconstruction
behavior. Both graph contexts were truncated; subsequent direct reads retrieved
the omitted decision. No agent invoked capture, created a proposal, or changed the
accepted knowledge store. All stores remained clean at their original revision;
no knowledge proposal branches were created.

The [machine report](retrieval-skill-split-20260926.json) contains native command
outputs, code diffs, independent grades, usage, source/trace hashes and separate
parent-Codex reviews. Preparation, skill, policy and grader hashes still matched
at review time. The local run directory is named retrieval-skill-split-20260925;
this report was finalized on September 26. No quota retry was needed in this batch.

The two preparation tests passed, and both new/updated skills passed the skill
validator. Runtime code was unchanged by this refactor; the earlier 52-test run
belongs to the generic-connection change and was not repeated here. Existing
historical reports were not rewritten. The capture skill's wording changed, but
these three sessions do not constitute a new capture evaluation.

These small synthetic trials support the intended retrieval/capture separation.
They do not guarantee instruction compliance in complex tasks, test every error
path, or isolate graph benefit. The boundary is skill guidance, not an enforced
read-only CLI permission. Synchronization may refresh local accepted data and the
index; retrieval does not author new knowledge. Reviews were not blind human reviews.
