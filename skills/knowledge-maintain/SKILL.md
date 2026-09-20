---
name: knowledge-maintain
description: Review knowledge-agent contribution branches or maintain accepted knowledge for duplicates, obsolete conditions and broken anchors. Execute on a requested proposal review or maintenance run; produce explicit decisions, correction proposals and acceptance status.
---

# Maintenance workflow

Choose the applicable route: **proposal review** starts at step 2; **accepted-node
maintenance** starts at step 3. Both start with step 1 and finish at step 6.
Do the inspections and report decisions; a tool report alone is not semantic review.

## 1. Establish the repository, revision and authority

Use the installed CLI and the supplied config consistently. `CONFIG` means that
path; omit `--config CONFIG` for the environment/default configuration. Read the
config to find `KNOWLEDGE_REPO`, accepted branch and provider. Establish whether
the request authorizes recommendations only, correction proposals, or acceptance.
Use existing standing authorization without asking again; this skill grants none.
Run `git -C KNOWLEDGE_REPO remote` to check for `origin`; use the knowledge repository
from config, not the coding project's Git repository.

```text
knowledge-agent --config CONFIG synchronize
knowledge-agent --config CONFIG status
```

Record the knowledge revision and stale state. If accepted Markdown is invalid or
the index is unavailable, report the concrete integrity/setup blocker. Do not certify
an old index as current or claim the normal proposal path can repair an accepted
snapshot that it cannot load. A stale snapshot can inform investigation, not final
acceptance. Do not modify the accepted checkout to bypass validation.

## 2. Review a contribution branch

```text
knowledge-agent --config CONFIG review BRANCH
```

Record `accepted_revision`, `proposal_revision`, `base_revision`, conflicts,
integrity errors and duplicate candidates. These are the exact commits under review.
Inspect what the proposal changes, including deletions, admission records and aliases:

```text
git -C KNOWLEDGE_REPO diff --name-status BASE_SHA PROPOSAL_SHA -- nodes aliases.json reviews
git -C KNOWLEDGE_REPO diff BASE_SHA PROPOSAL_SHA -- nodes aliases.json reviews
git -C KNOWLEDGE_REPO show PROPOSAL_SHA:NODE_PATH
knowledge-agent --config CONFIG read EXISTING_ID --revision ACCEPTED_SHA
```

Use actual paths returned by the diff. `read` reads accepted knowledge; inspect
proposed content using its committed Git files, not by assuming the index contains it.

For each changed claim, check and record:

- Admission: nontrivial to recover, not fully covered by an applicable skill,
  concrete action implication, and plausible reuse. Inspect skill overlap.
- Evidence: inspect referenced guidance, code, tests or experiments; distinguish
  verified results, reports and inferences. Unavailable evidence remains a gap.
- Scope: compare conditions, versions and deployment separately from code revisions.
- Duplicates: read each plausible existing candidate and compare conclusion and
  scope; similarity alone neither proves nor rules out equivalence.
- Graph/anchors: check that edge types express the supported relationship and
  anchor paths/symbols/revisions have the stated role. Verify merge redirects,
  rewritten references and preserved provenance; inspect unexpected deletions.

Classify every changed node as **acceptable**, **needs correction**, or **unresolved**
with reasons. A blocked/stale report prevents acceptance. If accepted history has
advanced, reconcile the contribution branch before local acceptance even when there
is no textual conflict. After any branch change, rerun this step and inspect new SHAs.

If changes are needed, use step 4. If acceptable, go to step 5. In recommendation-only
mode, finish with the review findings instead of mutating or accepting anything.

## 3. Inspect accepted knowledge independently

Use a JSON file mapping repository identities to actual code checkouts, for example
`{"orders":"C:/work/orders"}`. Do not fabricate mappings for unavailable repositories.

```text
knowledge-agent --config CONFIG validate
knowledge-agent --config CONFIG maintain --repositories MAP_FILE --duplicates
```

For known code changes or a changed shared constraint, execute the applicable form:

```text
knowledge-agent --config CONFIG review-impact --repo REPO --code-repo CODE_PATH --base OLD_SHA --head NEW_SHA
knowledge-agent --config CONFIG review-impact --repo REPO --path RELATIVE_PATH
knowledge-agent --config CONFIG review-impact --repo REPO --changed-id NODE_ID
```

Read each flagged node and its relevant neighbors at the indexed revision:

```text
knowledge-agent --config CONFIG read NODE_ID --revision SHA
knowledge-agent --config CONFIG context NODE_ID --all-statuses --depth 2 --max-nodes 20 --max-tokens 16000 --revision SHA
```

Impact follows incoming constrained_by/depends_on/supported_by relationships.
`related_to` supports exploration, not invalidation propagation. Check truncation
and record any deferred nodes. Check command revisions remain consistent; resync
and repeat affected comparisons if another operation changes the index.

Also inspect external/configuration/deployment conditions, including nodes without
anchors: a clean anchor scan is not a validity certificate. For a full run, obtain
the node count `N` from `status`; if nonzero, enumerate with `search --order weight
--all-statuses --limit N --candidates N` using the same config and revision, then read
the nodes in the requested scope. For a bounded run, report the scope and deferred
coverage. Missing code access and unavailable evidence are unresolved checks.

For each finding, decide the following before preparing changes:

| Finding after inspection | Decision |
|---|---|
| Same conclusion and conditions still supported | Retain; refresh verification only if actually checked. |
| Code moved, meaning unchanged | Update anchor after verifying the destination; retain conclusion. |
| Genuine condition/version change | Revise scope or mark `needs_review`; inspect dependent decisions. |
| Equivalent scoped claims | Propose a merged survivor retaining evidence, meaningful links and a retired-ID redirect. |
| Obsolete current advice with relevant history | Supersede/archive with explanation; preserve historical rationale. |
| Unavailable or contradictory evidence | Report uncertainty; propose `needs_review` where warranted. |

Never infer obsolescence from age, inactivity, low weight or orphan status alone.
If no changes are warranted, go to step 6 and report no changes; do not force a node.

## 4. Prepare corrections without changing accepted files

Read the existing node before editing; preserve its ID and relevant metadata/body.
Resolve retired IDs to their survivor. Write complete revised Markdown files in a
scratch directory and a manifest containing `nodes`, `operations`, `admission` and
optional `merges`. Each supplied ID needs an explicit `update` (or `create` only for
an actually new conclusion) and admission rationale. The admission declaration has
`id`, `existing_knowledge_search`, and four objects with `passes: true` and actual
`reason` text: `not_cheaply_recoverable`, `not_skill_duplicate`, `actionable`, `future_use`.
Document the value of preserving/revising historical advice when archiving it;
do not invent passing reasons for a claim that never qualified.

For a merge, supply an admitted revised survivor plus
`"merges": {"retired-id": "survivor-id"}`. The tool redirects affected references and
retains source provenance; you must preserve meaningful outgoing links and scope.
Do not merge different version-specific conclusions just because wording matches.

```text
knowledge-agent --config CONFIG validate --file REVISED_FILE
knowledge-agent --config CONFIG propose MANIFEST_FILE
```

Fix validation errors before retrying. Check `committed`; on failure preserve and
finish the existing worktree rather than creating another proposal. For corrections
to a pending contribution, amend the affected files in that contribution's isolated
worktree and commit there; do not create an unrelated proposal against accepted
knowledge that omits the original contribution. Return to step 2 after corrections.

## 5. Accept or submit within the authorized scope

Only proceed if semantic checks pass and acceptance/submission is authorized. Rerun
`review BRANCH` immediately beforehand; inspect changed revisions and repeat relevant
review if anything changed. Never substitute guessed SHAs or suppress stale errors.

**Local repository without origin:** use the exact reviewed revisions and rationale:

```text
knowledge-agent --config CONFIG accept BRANCH --reviewed-accepted ACCEPTED_SHA --reviewed-proposal PROPOSAL_SHA --reason "ACTUAL REVIEW RATIONALE"
```

Check `outcome` and `indexed`. If acceptance is committed but `indexed: false`, run
`rebuild-index` and verify `status`; do not merge again. On dirty-checkout, stale-review
or lock errors, preserve work and report the specific required resolution. Do not
delete a lock until its owning operation is confirmed stopped.

**Remote repository:** when submission is authorized, push the reviewed contribution
and create a request with a review body, or reuse its existing request:

```text
knowledge-agent --config CONFIG push BRANCH
knowledge-agent --config CONFIG open-request BRANCH --title "Knowledge maintenance: TOPIC" --body-file REVIEW_BODY_FILE
```

Push must succeed before request creation. A request is not a merge. Remote merge
uses the configured provider's authorized review/merge workflow; this CLI has no
remote merge command. Recheck the accepted SHA at that boundary and serialize final
admission. Do not assume posting a review, creating a PR or merging is authorized
merely because an investigation was requested. Report the achieved stage on failure.

## 6. Report decisions and actual completion

Report reviewed accepted/proposal revisions, checked scope, per-node decisions and
reasons, corrections/retired IDs, unresolved evidence or deferred coverage, and the
achieved state: recommendation only, no changes, pending proposal, submitted request,
or accepted locally. Include branch/request references and index status when relevant.
Distinguish a proposed status change from an accepted one. State the next action.

A scheduler must invoke accepted-node maintenance independently of new proposals;
installing this skill does not schedule it.
