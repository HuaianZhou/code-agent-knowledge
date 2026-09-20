# Code Agent Knowledge

A structured knowledge graph for capturing and reusing project tribal knowledge
from conversations with coding agents.

Tribal knowledge includes the unwritten constraints, human corrections, failed
approaches and validated discoveries that emerge while an engineer and a coding
agent work together. This project turns the useful, actionable lessons from those
conversations into durable knowledge that future agents and developers can reuse,
reducing repeated investigations and mistakes.

Knowledge is stored as reviewed Markdown nodes in Git, with structured metadata,
evidence, code anchors and explicit relationships. Those relationships form a
graph: decisions and pitfalls can link to shared constraints, and retrieval can
follow those links in both directions to surface relevant connected knowledge.
It is not a transcript archive or an automatically generated map of the codebase.
The working agent selects qualifying knowledge from its conversation and task
evidence; the tool validates, indexes, retrieves and prepares it for review.

The current implementation is a Python CLI with a rebuildable local index. No
central database or Basic Memory deployment is required. See the
[discussion spec](knowledge-agent-spec.md), [implementation plan](PLAN.md) and
[node/manifest schema](docs/schema.md).

## Install and try the complete local loop

Requires Python 3.11+ and Git. From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m examples.run_demo --directory .demo
.\.venv\Scripts\knowledge-agent.exe --config .demo/reader-client/config.json search journal
.\.venv\Scripts\knowledge-agent.exe --config .demo/reader-client/config.json context kn-writer-change --max-tokens 12000
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On POSIX use `.venv/bin/python` and `.venv/bin/knowledge-agent`. The demo requires a
fresh destination. It creates separate code/knowledge repositories and a bare Git
remote, proposes synthetic human-reported knowledge, runs review, explicitly accepts
the fixture, syncs a second reader, traverses A → B ← C, and detects moved code.
Full results are written to `.demo/results.json`. It does not access a hosted service.

## Configure a real knowledge repository

Keep knowledge in its own repository with `nodes/*.md` (nested paths allowed) and
optional `aliases.json`. Start from an existing committed branch or clone a remote:

```text
knowledge-agent --config /path/to/client/config.json initialize --repo /path/to/knowledge --remote GIT_URL --branch main
knowledge-agent --config /path/to/client/config.json synchronize
```

Omit `--remote` to configure an existing repo. Default configuration is
`~/.knowledge-agent/config.json`; override with `--config` or
`KNOWLEDGE_AGENT_CONFIG`. Use a separate config directory per knowledge repository.
Git uses your existing credentials. Proposal commits use your configured Git identity;
if missing, the worktree and staged changes remain available and `committed` is false.

The accepted snapshot is a commit, independent of dirty files in the checkout.
Sync fetches origin and advances a private accepted ref only for fast-forward history;
it never resets a developer's checkout. Offline sync retains the last accepted
revision and reports stale state. Explicit `rebuild-index --revision SHA` pins a
historical snapshot. Pass the exact returned SHA through `--revision` on retrieval
to fail if another operation replaces that snapshot. One current index per client
is supported; use separate client configs for simultaneous independently pinned tasks.

## Retrieval and embeddings

Every command emits JSON with a revision. Examples:

```text
knowledge-agent search "recovery after a writer deploy" --repo orders
knowledge-agent search --order weight --tag journal
knowledge-agent search "journal" --order candidate-weight --candidates 30 --limit 5
knowledge-agent read kn-journal-compatibility
knowledge-agent lookup-anchor orders writer.py --symbol State
knowledge-agent context kn-writer-change --direction both --depth 2 --max-nodes 12 --max-tokens 12000
knowledge-agent validate
knowledge-agent status
```

Active nodes are the retrieval default. `--status needs_review` includes review
warnings; repeat `--status` or use `--all-statuses` for history. Tags use all-of
matching, repeated types use any-of matching. Scope repository filtering includes
cross-repository nodes. Agents still check conditions and deployed versions.

`--order weight` ranks the **entire metadata-filtered set**, even if a query is
supplied. `candidate-weight` first selects the query's top candidate set and then
ranks that set by importance; it is never described as global importance ordering.
Context uses breadth-first traversal with stable ordering, cycle detection and
deduplication. Every result includes its relationship path. Status/scope-filtered
nodes are not traversed. Depth/node/token exhaustion is explicit. Token budgeting
uses conservative UTF-8 byte counts of node records, not a model tokenizer; wrapper
metadata is additional. Increase the budget when full node metadata is verbose.

Default `lexical` embeddings use deterministic feature hashing for an offline demo.
They are explicitly **not semantic** and cannot reliably find paraphrases. Production
semantic mode is optional and runs locally:

```text
pip install -e ".[semantic]"
knowledge-agent --config /path/to/semantic-client/config.json initialize --repo /path/to/knowledge --backend sentence-transformers --model APPROVED_MODEL --model-revision IMMUTABLE_MODEL_REVISION
```

Choose an approved Sentence Transformers model and immutable revision; the first
use may download model files. No node text is sent to an embedding API and remote
model code is disabled. Long payloads are token-chunked and averaged. Payload v1
contains title, type, tags and full body; keep situation/action/evidence in the body.
IDs and anchors are exact metadata, outside the embedding payload. The implementation
uses the [Sentence Transformers API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
and [sqlite-vec](https://github.com/asg017/sqlite-vec).

SQLite stores node IDs, payload hashes, normalized vectors, metadata, graph/anchor
data, model/revision/dimensions/configuration and knowledge SHA. sqlite-vec performs
exact cosine scans over the filtered candidate set; no custom vector engine. This
MVP favors correctness at small-repo scale over ANN performance. Metadata-only
changes do not re-embed. Deleted entries are removed. A configuration/payload policy
change rebuilds all vectors. One transaction publishes the complete snapshot;
concurrent writers serialize, failed writes roll back, and readers see one coherent
snapshot. `rebuild-index --force` recreates derived content.

## Extraction and review

The working agent, not the CLI, extracts and judges knowledge. Bundled skills:
[extraction/usage](skills/knowledge-extract/SKILL.md) and
[maintenance](skills/knowledge-maintain/SKILL.md). Install these folders in your
agent's skill directory, then add a host instruction to invoke extraction before
the final task response while conversation evidence is available. Installation
alone does not guarantee execution. The explicit integration boundary is:

```text
knowledge-agent task-end /path/to/proposal.json
knowledge-agent review knowledge/proposal-ID
```

An empty manifest reports zero writes. Qualifying nodes require all admission gates
with reasons and a recorded existing-knowledge search. Proposals are committed in
separate worktrees under the client's state directory. Each supplied node also needs
an explicit `create` or `update` entry in the manifest's `operations` map. Updates
must reference an existing ID in the accepted snapshot; creates must use a new ID.
Invalid operations fail before any proposal writes. Existing manifests need this
field added. Search/read existing knowledge first to assess semantic overlap as well
as ID existence. Review refreshes the accepted
state and flags concurrent ID conflicts, integrity errors and duplicate candidates
with both scopes visible. Similarity does not establish equivalence. Rerun review
immediately before a serialized host-managed merge; a report is not authorization
or protection against a later concurrent merge. The tool never auto-merges.

Push and request creation are distinct explicit commands:

```text
knowledge-agent push knowledge/proposal-ID
knowledge-agent open-request knowledge/proposal-ID --title "Retained journal compatibility" --body-file review.md
```

Set `provider` in config to `github` or `gitlab` and authenticate `gh` or `glab` for
the second command. Requests are drafts. No provider is selected by default. These
optional adapters are not exercised against a live service by the local tests.

## Maintenance

```text
knowledge-agent review-impact --repo orders --path writer.py
knowledge-agent review-impact --repo orders --code-repo /path/to/orders --base OLD_SHA --head HEAD
knowledge-agent review-impact --repo orders --changed-id kn-journal-compatibility
knowledge-agent maintain --repositories /path/to/repositories.json --duplicates
```

The repositories file maps identities to checkouts, e.g. `{"orders":"/path/to/orders"}`.
Impact follows incoming constrained_by/depends_on/supported_by edges and suggests
needs_review; related_to does not propagate. Git rename detection proposes anchor
moves. Maintenance reports missing paths/revisions, changed anchored code and missing
symbols (lexical check, not a language parser). Reports do not silently rewrite
claims or prove validity; propose reviewed changes through the same workflow.
`--duplicates` compares accepted nodes and reports similarity candidates, with
different scopes visible; it never merges automatically.

A host scheduler can periodically invoke `maintain`, persist its JSON and invoke
the maintenance skill for findings and external-condition checks. Scheduler choice,
notifications and reviewer permissions belong to the deployment; none is silently
installed. Node merges redirect inbound references, preserve sources and leave an
ID alias. Inactivity never lowers weight or proves obsolescence.

## Validation and remaining deployment choices

Tests cover schema/link failures, both-direction traversal, cycles and budgets,
filtering/order semantics, anchor lookup, index rollback/concurrency, metadata-only
updates/deletions/rebuild, immutable revisions, isolated contributions, merge aliases,
latest-state duplicate/conflict review, code movement and offline Git synchronization.
The demo data is hand-authored; see the separate [behavioral evaluation protocol](docs/evaluation.md).
No claim of measured agent productivity or automatic semantic deduplication is made.

The actual Kiro draft was not supplied. Company-approved embedding model, remote and
review policy, task-end host integration, scheduler, real evaluation tasks and adoption
thresholds remain deployment choices. CLI is implemented; an MCP adapter is optional
future work. The default dependency/test run exercises lexical mode; semantic mode
requires the optional model installation and project-specific retrieval evaluation.
