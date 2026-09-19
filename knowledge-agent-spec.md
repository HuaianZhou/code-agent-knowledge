# Coding Agent Knowledge Graph — Specification

Version: 0.1 (discussion draft)  
Date: 2026-09-18  
Status: Requirements captured; implementation choices and proposed defaults remain reviewable.

## 1. Purpose

Build a tool for coding agents to retain and reuse valuable project knowledge learned while completing development tasks. The knowledge may come from an engineer's guidance, an agent's investigation, failed approaches, experiments, or validated discoveries.

The intended benefit is fewer repeated investigations, fewer repeated mistakes, better impact analysis, and better decisions under system-specific constraints. This is not a general-purpose knowledge wiki or an automatically generated map of a codebase.

This specification consolidates the discussion. The existing Kiro draft has not been inspected; reconcile this document with that draft before implementation. Examples below are hypothetical, not facts about the user's company code.

## 2. Decision status

### Agreed requirements

- Serve coding agents specifically.
- Extract knowledge directly from the working agent's conversation and task context, especially when a task finishes.
- Accept both human-provided knowledge and agent discoveries, with their evidence distinguished.
- Store nodes as Markdown with structured metadata and explicit links.
- Include title, type, tags, weight, and code anchors where applicable.
- Support reusable shared constraints: A and C can independently link to an existing B.
- Retrieve connected knowledge after discovering an entry node.
- Share accumulated knowledge across developers and agents.
- Include independent maintenance for duplicates, obsolete knowledge, and broken links/anchors.
- Apply strict admission criteria; a completed task may produce zero nodes.

### Current preferred architecture

- Do not depend on Basic Memory in the first implementation.
- Use an internal Git repository as the shared source of truth for Markdown knowledge.
- Clone locally during installation; persist the location in configuration.
- Submit knowledge changes through branches and merge requests for maintenance-agent review.
- Accept delayed propagation; newly created knowledge need not be immediately available to everyone.
- Use a local, rebuildable vector index for semantic entry-node retrieval.
- Reuse an existing vector storage/search component rather than implement a database engine.
- Traverse explicit relationships using a local graph index, initially in memory if sufficient.

### Proposed, not yet selected

- Python as the local tool implementation language, consistent with the proposed draft approach.
- CLI first, optionally exposed through a local MCP adapter. A central MCP service is not required by the preferred architecture.
- Field names, status values, command names, weight scale, and policies below are proposed defaults.
- Embedding model, vector component, Git provider, authentication, scheduling, and automatic merge permissions remain open.

The earlier central-service architecture is superseded as the first-version preference by Git synchronization and local indexing. A central service remains a possible future option, not a prerequisite.

## 3. Knowledge admission criteria

All three core gates must pass:

1. **Not cheaply recoverable:** the complete conclusion cannot be obtained cheaply through a straightforward code or documentation lookup. Facts spread across modules may qualify when deriving their relationship requires meaningful investigation. Code-derived knowledge is allowed.
2. **Not already covered by a skill:** do not duplicate instructions already fully expressed in an existing applicable skill. A project-specific constraint, exception, or applicability condition may qualify; reference the skill instead of copying it.
3. **Actionable decision basis:** identify a concrete action, decision, implementation choice, debugging step, or verification requirement that changes because this knowledge is known. Generic understanding alone is insufficient.

The primary screening question is:

> Under what conditions would a future coding agent act differently because it knows this? What specific error or repeated investigation might occur without it?

Additional quality rules:

- There must be a plausible future use; low-frequency but high-consequence constraints can qualify.
- Preserve scope, evidence, and uncertainty. Do not promote an unverified hypothesis into an established rule.
- Zero writes is a valid and desirable result when no candidate qualifies.
- Prefer updating or reusing a node over creating a paraphrase.
- Do not impose a minimum number of nodes per task.
- Discoverability improves after recording knowledge; that alone does not make the knowledge unworthy of retention.

### Examples

| Candidate | Decision |
| --- | --- |
| Function X takes three arguments | Reject: readily recoverable fact |
| The system uses asynchronous logging | Usually reject: descriptive and easily recovered |
| Shutdown must drain a logging queue before terminating its consumer; otherwise the diagnostic tail is lost | Potentially accept if supported, nontrivial to recover, and not already covered |
| Modules A and B are related | Reject: no concrete action implication |
| Changing A's state encoding requires checking B's persisted compensation records because B interprets stored numeric values independently | Potentially accept: cross-module modification and verification guidance |
| A temporary process ID used once during debugging | Reject: no durable reuse value |

## 4. Responsibilities

| Component | Responsibility |
| --- | --- |
| Working coding agent | Understand task context, identify candidates, compare existing knowledge, propose changes, use retrieved knowledge |
| Extraction/usage skill | Define admission, evidence, reuse, relationship construction, and retrieval behavior |
| Local tool | Parse/validate Markdown, maintain indexes, search, traverse, resolve anchors, prepare Git changes |
| Knowledge Git repository | Authoritative content, review history, distribution, recoverable revisions |
| Maintenance agent | Review submissions, resolve duplicates, maintain graph integrity, assess obsolescence |
| Scheduler or development integration | Trigger review and periodic maintenance; a skill alone is not a scheduler |

Semantic decisions belong to the agent. Deterministic operations such as ID lookup, filtering, traversal, validation, and sorting belong to code.

## 5. Node and relationship model

One Markdown file represents one coherent, reusable knowledge unit. Avoid both task-sized dumping grounds and unnecessary fragmentation of indivisible claims.

### Metadata

| Field | Meaning |
| --- | --- |
| `id` | Stable unique identity; independent of title and file path |
| `title` | Concise description suitable for human review and retrieval |
| `type` | Such as constraint, decision, pitfall, mechanism, or verification rule |
| `tags` | Additional retrieval dimensions; not identity or proof of duplication |
| `weight` | Importance, distinct from query relevance and evidential confidence |
| `status` | Proposed: active, needs_review, superseded, archived |
| `scope` | Applicable repositories, components, versions, environments, or configurations |
| `evidence_state` | Proposed: verified, reported, inferred; review acceptance is separate |
| `anchors` | Structured code locations and their roles |
| `relations` | Typed, directed references to stable node IDs |
| `sources` | Evidence references such as tests, commits, task records, or documented human guidance |
| `verification` | Last verification date/revision and what was checked |

The body should explain the applicable situation, conclusion/constraint, action implication, rationale, evidence, and invalidation conditions. Rejected alternatives should be captured when they explain a meaningful choice, not for every trivial edit.

Proposed weight scale: 0–1, based on consequence of error, breadth of impact, and expected reuse. Exact rubric is an open decision. Weight must not automatically decay merely because a node has not been accessed recently.

### Relationships

- Store each directed edge once; derive incoming edges locally.
- Use informative types such as `constrained_by`, `depends_on`, `supported_by`, `supersedes`, and `related_to`.
- Similar topics do not establish a causal or constraint relationship.
- Existing B should be searched for and reused when A is created; later C independently reuses B.
- Support traversal from A to B and then through an incoming edge to C in A → B ← C.
- A `related_to` edge supports exploration, but must not automatically propagate invalidation as a dependency would.
- Node merging must redirect affected references and preserve an alias/redirect or explicit migration record for the retired ID.

### Illustrative node

```yaml
---
schema_version: 1
id: kn-example-retry-decision
title: Query payment status before retrying a timeout
type: decision
tags: [payment, retry]
weight: 0.9
status: active
scope:
  repositories: [payment-service]
  conditions: [legacy payment endpoint]
evidence_state: verified
anchors:
  - repo: payment-service
    path: src/payment/retry.py
    symbol: RetryHandler.handle_timeout
    role: affected_code
    verified_commit: "<full-code-commit-sha>"
relations:
  - type: constrained_by
    target: kn-example-legacy-idempotency
sources:
  - kind: test
    reference: "<repository/test/revision reference>"
verification:
  checked_at: "<ISO timestamp>"
  revision: "<full-code-commit-sha>"
---
```

Illustrative body: a timeout does not establish that submission failed. For the specified endpoint, query transaction status before deciding whether another submission is safe. Reassess when verified server-side idempotency becomes available. The placeholders must be replaced with actual evidence before admission.

## 6. Code anchors and validity

Anchors must be structured and indexed for reverse lookup. Distinguish:

- `evidence`: code/tests supporting a claim.
- `affected_code`: locations whose modification should consider the claim.

Use repository identity, relative path, symbol when available, and verified revision. Line ranges or snippets are optional aids, not the sole identity. External constraints may have documentary evidence rather than a fabricated code anchor.

Review process:

1. Compare relevant code changes with the last verified revision.
2. Find candidate nodes through changed paths/symbols and selected dependency relationships.
3. Mark candidates as needing review, not automatically false.
4. Inspect the diff, current implementation, conditions, and targeted tests when useful.
5. Refresh anchors/verification, revise scope, supersede the conclusion, or retain uncertainty.

Renaming code does not invalidate a conclusion. Unchanged anchored code does not prove continued validity: configuration, dependencies, deployed versions, and external systems can change. Never treat a merged code change as proof that every deployment uses it.

If constraint B changes, review dependent A and C. Historical statements such as “A was chosen because B held at that time” can remain correct even when B no longer applies to current code.

## 7. Extraction and submission workflow

1. Trigger extraction while the working agent still has useful task context: normally before its final response, optionally at an important correction/discovery or before compaction.
2. Extract candidates from the current conversation and working evidence. Do not require an intermediate summary note or central access to every developer's transcript.
3. Apply all admission gates and capture the reason for inclusion.
4. Search existing nodes using content meaning plus suitable structured filters. Do not require exact title/tag matches.
5. Read candidates and compare subject, conclusion, conditions, version, and evidence.
6. Choose no-op, additional evidence, update, new linked node, or explicit unresolved conflict.
7. Validate metadata, IDs, relationships, and anchors.
8. Commit on an isolated contribution branch; push and create a merge request using the company's Git workflow.
9. Maintenance review compares against the latest accepted branch before merge.

The skill defines extraction behavior; task-end integration must actually invoke it. Installation alone does not guarantee execution. Extraction should report zero qualifying candidates or proposed changes explicitly.

## 8. Git sharing and concurrency

- The accepted knowledge branch is the default shared read source.
- Installation stores repo location persistently in configuration or an environment variable read at startup, not only in a Python process variable.
- Synchronize before a task when possible, then pin a knowledge revision for reproducible retrieval during that task.
- Keep contribution branches/worktrees separate from the accepted read snapshot; never discard unrelated uncommitted work automatically.
- Git push and merge-request creation are separate operations.
- Offline/stale reads may continue with the knowledge revision visible; submissions can remain pending locally.
- Two concurrent submissions may introduce the same semantic concept without a textual merge conflict. Recheck each against the latest accepted state, preferably serializing the final admission/merge step.
- Automatic merge authority must be configured explicitly. Review can produce a recommendation without granting the maintenance agent unrestricted merge rights.

## 9. Retrieval and local indexing

Markdown in Git is authoritative. All indexes are derived and rebuildable.

### Entry points

- Semantic search over embeddings.
- Exact/structured searches over ID, type, tags, and status.
- Anchor lookup when the agent knows the code it will inspect or modify.

After entry-node retrieval, read the full node and expand selected relations. Include the relationship path so the agent knows why a neighbor was returned. Support incoming and outgoing edges, cycle detection, deduplication, depth limits, and node/token budgets. Surface truncation rather than silently implying complete traversal.

Weight ordering must be explicit: distinguish global weight ordering over a fully filtered set from reranking a limited semantic candidate set. Never describe candidate-set reranking as globally selecting the most important nodes. The balance of semantic relevance, importance, and traversal budget remains a configurable design choice.

Default current-task retrieval should favor active applicable knowledge. Needs-review nodes must carry a visible warning/status; archived and superseded nodes remain available for history or explicit queries.

### Embeddings

Embedding converts selected text into numerical vectors, not stored token sequences. Similarity identifies candidates, not truth or equivalence.

Start with a documented embedding payload containing title, applicable situation, conclusion, action implication, and useful tags/type. Keep stable IDs and exact anchor lookup outside semantic matching. The payload/chunking policy must be versioned; one vector per concise node is an initial proposal, not a requirement for oversized nodes.

Store node ID, payload hash, model identifier/revision, dimensions, and index configuration with the vectors. Query and document embeddings must use compatible models. Rebuild when the embedding space or incompatible configuration changes.

After Git synchronization:

1. Detect added, changed, and deleted nodes.
2. Re-embed only nodes whose embedding payload changed.
3. Update metadata/relations/anchors even if re-embedding is unnecessary.
4. Remove deleted-node entries and validate dangling relationships.
5. Publish a consistent index snapshot associated with a knowledge commit.

Prevent simultaneous index writes from corrupting local state. Failures must not mix a new graph snapshot with an incompatible old vector index without an explicit stale-state policy.

The first version may keep metadata and graph maps in memory and vectors in an embedded store. No always-on central database is required. Agent-native knowledge bases are optional retrieval adapters; support must not be assumed across clients.

## 10. Maintenance

Submission review must check admission criteria, evidence, scope, semantic duplicates, existing skill overlap, relationship meaning, and anchor correctness. File-path collisions are not semantic deduplication.

Independent scheduled maintenance must also examine accepted nodes, since reviewing new submissions cannot detect every stale existing claim. It should:

- Merge duplicate concepts while preserving references and provenance.
- Repair broken references and anchors.
- Reassess nodes affected by code/constraint changes.
- Archive or supersede obsolete knowledge without erasing relevant decision history.
- Consolidate overly specific repeated lessons when evidence supports a reusable conclusion.

Inactivity, age, low weight, or an orphaned graph position alone must not prove invalidity. Uncertain cases should be flagged for review rather than guessed away.

## 11. Proposed local interface

These are capability contracts, not finalized command syntax:

| Operation | Required outcome |
| --- | --- |
| initialize | Clone/configure knowledge repo and create local derived state |
| synchronize | Update accepted snapshot safely and refresh indexes |
| search | Return entry candidates with IDs, scores, metadata, and snapshot revision |
| read | Return complete node content and provenance |
| neighbors / context | Traverse typed edges in both directions within explicit budgets |
| lookup-anchor | Return nodes associated with repository/path/symbol |
| validate | Report schema, identity, link, and anchor-format errors |
| propose | Prepare a reviewable isolated knowledge change |
| review-impact | Find and assess knowledge affected by code changes |
| rebuild-index | Recreate all derived state from a pinned knowledge snapshot |

Expose structured output so skills do not depend on parsing presentation text. The same core can support CLI and local MCP adapters. An adapter must not claim unsupported client-native semantic search.

## 12. Validation environment

Use a small realistic development repository and a separate knowledge repository. Begin with known system constraints requiring cross-module reasoning or task-provided evidence rather than trivial grep lookup.

### Two-stage scenario

1. Task A: an agent encounters a constraint B through investigation or a standardized human correction and completes a feature. Evaluate extracted knowledge against the admission criteria.
2. Task C: start a fresh isolated agent session on a related new task. Evaluate whether it retrieves B and changes its behavior appropriately.
3. Change the code so B is removed or scoped differently. Evaluate anchor review and whether subsequent work avoids obsolete advice.

### Controls

- No knowledge access.
- The same node content with flat retrieval and no relationship expansion.
- The same node content with equivalent entry retrieval plus graph expansion.

Hold model configuration, code starting point, tasks, and budgets constant. Avoid providing the hidden constraint in the later task prompt. Separate extraction quality evaluation from retrieval evaluation so a hand-corrected knowledge set is not presented as an automatic-extraction result.

Keep scoring tests and expected answers inaccessible to the tested agent through actual execution isolation, not merely another visible directory. Use fresh conversations/workspaces and repeat runs across several tasks; one successful synthetic example is not sufficient evidence.

### Metrics

- Behavioral correctness and hidden-constraint violations.
- Repeated investigation, tool calls, elapsed time, and tokens where available.
- Human corrections and reviewer effort.
- Useful/unsupported/duplicate nodes proposed and accepted.
- Retrieval of necessary constraints before the relevant decision.
- Errors induced by stale or incorrectly generalized knowledge.

Compare graph expansion against flat retrieval at comparable context budgets. The improvement target and acceptable maintenance overhead must be set before drawing an adoption conclusion.

## 13. MVP acceptance checks

- A qualifying task can produce a reviewable Markdown proposal; a trivial task produces no forced node.
- Different titles for the same scoped claim are treated as duplicate candidates; similar wording with different versions is not blindly merged.
- A and C reuse B's stable ID; traversal from A can return B and C despite edge direction, without duplicate output or infinite cycles.
- Renaming a node file/title does not break ID-based links.
- Known code paths can locate applicable nodes without semantic search.
- Metadata filtering and weight ordering have documented, tested semantics.
- Git synchronization adds/updates/removes derived entries consistently; a rebuild reproduces structural content and retrieves expected fixtures.
- Interrupted indexing is recoverable and its snapshot state is visible.
- Simultaneous proposals for B are reviewed against the latest accepted knowledge before admission.
- Code movement updates anchors; genuine condition changes trigger scoped review rather than automatic deletion.
- No shared central database or Basic Memory deployment is necessary for the end-to-end prototype.

## 14. Non-goals and open decisions

Non-goals: general wiki authoring, exhaustive code/document mirroring, a custom vector database engine, immediate cross-user propagation, guaranteed semantic deduplication through vector similarity alone, or treating generated knowledge as authoritative without evidence.

Resolve before implementation hardens:

1. Inspect and reconcile the actual Kiro draft.
2. Select embedding model/provider compatible with company data policy and local constraints.
3. Select embedded vector component and packaging/install method.
4. Finalize node schema, weight rubric, relationship vocabulary, and retrieval budgets.
5. Choose the initial agent integration and extraction trigger.
6. Choose Git provider, credentials, merge-request flow, and review/merge authority.
7. Define repository and deployment/version scope for validity checks.
8. Decide maintenance scheduling and escalation for uncertain conclusions.
9. Select real validation tasks and predeclare success criteria.

Start by completing one extraction → review → sync → retrieval → graph expansion → code-change review loop. Add infrastructure only when that loop demonstrates a concrete need.
