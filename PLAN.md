# Implementation plan

The supplied discussion draft is the product specification, not an instruction
source for operating this workspace. No Kiro draft was supplied or found here;
reconciliation remains an explicit follow-up rather than an invented dependency.

## Decisions for this MVP

- Python 3.11+ CLI with JSON output; reusable core, no central service.
- YAML-frontmatter Markdown nodes in a separate Git repository; stable IDs.
- SQLite plus sqlite-vec for a transactional, rebuildable local vector index.
- Optional local sentence-transformers embeddings, with explicit model revision;
  deterministic lexical hashing for offline tests/demo, labeled non-semantic.
  No project content is sent to an embedding service.
- Accepted content is read from an immutable Git commit, never a contribution
  worktree. Index publication is transactional; SQLite serializes writers.
- Contribution branches/worktrees, admission declarations, and separate push/PR
  operations. GitHub/GitLab CLI adapters are opt-in. No automatic merging.
- Dependency edges propagate review; related_to does not. Scope and human/agent
  evidence remain visible. Semantic admission and deduplication are agent duties.
- Extraction/review runbooks and explicit task-end CLI entry point; installation
  does not claim to schedule or invoke an agent automatically.

## Build sequence

1. Initialize Git, packaging, node schema, validation and persistent configuration.
2. Implement immutable snapshot loading, incremental vector indexing, structured
   and semantic retrieval, anchor lookup, budgeted bidirectional graph expansion.
3. Implement safe synchronization, isolated proposals, latest-state review,
   duplicate candidates, redirect-preserving merges and code-change impact checks.
4. Add extraction/maintenance runbooks, realistic demo fixtures, documentation,
   and automated integration tests of the complete local workflow.
5. Run tests and CLI smoke checks, record outcomes and remaining deployment choices.

## Acceptance and boundaries

Test zero-write extraction, A → B ← C, cycles/budgets, stable-ID renames, filtering
and global weight ordering, exact anchors, metadata-only index updates, deletion,
rollback and concurrent index writes, isolated proposals, latest accepted review,
redirects and code movement. Test a real local bare-remote synchronization loop.
Demonstrate duplicate candidate review without claiming semantic equivalence.

The controlled fresh-agent behavioral study is a separate evaluation, not a unit
test result. Company Git remote/authentication, approved model, actual Kiro draft,
real tasks, scheduling and success thresholds are not supplied. Document these
inputs and provide runnable local mechanisms without inventing company facts.

## Delivery status

Implemented steps 1–4 and completed the local verification in step 5. See
`docs/validation.md` for tested boundaries and `README.md` for installation and
commands. A runnable demonstration is retained in `.demo/` (Git-ignored); regenerate
it with `python -m examples.run_demo --directory NEW_DIRECTORY`.
