# Nodes and proposal manifests

Nodes live under `nodes/` in the **knowledge** repository. Each file contains YAML
frontmatter between `---` lines and a nonempty Markdown body. IDs are stable and
independent of paths. Unknown metadata is retained for project extensions.

Required fields: `schema_version: 1`, `id`, `title`, `type`, `tags`, `weight`,
`status`, `scope`, `evidence_state`, `anchors`, `relations`, `sources`, `verification`.
Types: constraint, decision, pitfall, mechanism, verification_rule. Statuses:
active, needs_review, superseded, archived. Evidence: reported, inferred, verified.
Weight is finite in [0,1]; suggested rubric: 0.9 severe consequence/broad reuse,
0.6 recurring local constraint, 0.3 narrow but meaningful action. It is neither
confidence nor relevance and never decays automatically.

`scope` requires string lists `repositories` and `conditions`; an empty repository
list means cross-repository. Extra version/environment fields are preserved. Only
repository filtering is deterministic; the agent assesses conditions and versions.
`anchors` entries require repo, safe relative path, role (`evidence` or
`affected_code`) and full verified_commit SHA; symbol is optional. Sources require
kind (test, commit, task, human, document, experiment) and a reference. Verified
evidence additionally requires verification.checked_at, revision and checked.
Reported/inferred nodes may have empty verification. Evidence is not review approval.

Relations contain type and target stable ID. Types: constrained_by, depends_on,
supported_by, supersedes, related_to. Only the first three propagate dependency
review. Directed edges are stored once. `aliases.json` maps retired IDs to live IDs;
the validator rejects dangling links, collisions and alias cycles.

Body: explain situation, conclusion, concrete action, rationale/evidence, uncertainty
and invalidation conditions. Maximum 24,000 characters per coherent node. Do not
paste a transcript or copy a skill. Use the required fields above when composing
a node; preserve additional metadata when updating an existing node.

The `propose` / `task-end` manifest has this shape (node paths resolve relative to
the manifest; admission text must contain actual reasoning):

```json
{
  "nodes": ["candidate.md"],
  "operations": {"kn-journal-compatibility": "create"},
  "admission": [{
    "id": "kn-journal-compatibility",
    "not_cheaply_recoverable": {"passes": true, "reason": "Combines independent deployment guidance with two readers of retained state."},
    "not_skill_duplicate": {"passes": true, "reason": "No applicable skill covers this project's retained journal contract."},
    "actionable": {"passes": true, "reason": "Preserve numeric encodings or migrate records and coordinate readers."},
    "future_use": {"passes": true, "reason": "Both writer and recovery changes need this check."},
    "existing_knowledge_search": "Compared accepted journal nodes, scope and evidence; no equivalent claim found."
  }],
  "merges": {}
}
```

Zero candidates: `{"nodes": [], "admission": []}`. A merge supplies a revised,
admitted survivor plus `"merges": {"retired-id": "surviving-id"}`. Existing source
provenance is retained, affected edges are rewritten, and the retired ID redirects.
Gate declarations are auditable agent judgments; code cannot prove their truth.

Every supplied node requires an explicit entry in `operations`: `create` requires
an unused ID; `update` requires an existing ID in the accepted snapshot. Missing,
extra or invalid operations are rejected before creating a branch or writing proposal
files. Older nonempty manifests must add this field; there is no implicit upsert.
Updates retain the existing file path and stable ID, even if the title changes.
Retired IDs cannot be reused; read the redirect and explicitly update the surviving ID.
For merges, specify the survivor's operation; reference rewrites are handled by the tool.

Search and read existing knowledge before selecting the operation. ID existence
does not detect equivalent claims with different IDs: the agent must compare their
meaning, scope, versions and evidence. The operation check uses the pinned accepted
snapshot; review still checks concurrent changes against the latest accepted state.
