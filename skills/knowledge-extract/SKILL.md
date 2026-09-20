---
name: knowledge-extract
description: Retrieve and propose durable project knowledge for coding tasks using an installed knowledge-agent CLI and configured knowledge repository. Use at task start or task completion when this project knowledge workflow is enabled.
---

Use the working conversation and actual evidence directly. The CLI does not read
transcripts or make semantic admission decisions. Read `knowledge-agent --help`
and the repository's `docs/schema.md` for node and manifest details when writing.

At task start, run `knowledge-agent synchronize` when possible, record the returned
revision, and use `--revision SHA` on retrieval calls to detect snapshot changes.
Offline retrieval is allowed with revision and stale state visible. Search by
meaning and scope, or use `lookup-anchor` for known paths. Read complete nodes and
expand `context` across informative relationships within a budget. Conditions and
deployment versions require agent judgment; repository filtering alone is not
proof of applicability. Include `needs_review` explicitly when useful and preserve
its warning. Lexical mode is not semantic retrieval.

Before the final task response, evaluate candidates from the current context:

- Is the complete conclusion costly enough to recover to justify retention?
- Is it absent from applicable skills, or a meaningful scoped exception to one?
- What concrete future decision, action, or verification does it change?
- What plausible reuse, evidence, uncertainty and invalidation conditions exist?

Zero qualifying candidates is normal: submit an empty manifest to `task-end` and
report zero writes. Never invent a lesson to meet a quota. Search existing nodes
before proposing content; compare conclusion, conditions, versions and evidence,
not title or tags alone. Prefer no-op, added evidence, or an update over paraphrases.
Reuse stable IDs for shared constraints. Link causal/constraint edges only when
evidence supports that meaning; preserve unresolved conflicts explicitly.

Read the selected existing node before updating it, preserving its stable ID.
Write Markdown nodes and a manifest containing gate rationales, the existing
knowledge search, and an `operations` map assigning each supplied ID `create` or
`update`. Update requires an existing ID in the accepted snapshot; create requires
an unused ID. A failed update is not permission to create a replacement: resolve
the intended ID or redirect first. Distinguish human reports, inferences and verified results. Do
not fabricate anchors or promote a passing code change into deployment evidence.
Run `task-end MANIFEST` to validate and prepare an isolated committed proposal;
check `committed` and preserve the worktree on failure. Report the branch and
evidence gaps. This skill does not authorize pushing or opening remote requests;
use those commands only within the user's existing sharing authorization.
For a local-only knowledge repository, leave the branch for `review` and explicit
`accept`; no GitHub repository, push or pull request is required. `setup` can create
the local knowledge repository and persistent configuration when requested.

Installation does not invoke this skill automatically. A host task-end instruction
or agent integration must actually call it while conversation context is available.
