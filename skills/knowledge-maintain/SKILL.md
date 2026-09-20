---
name: knowledge-maintain
description: Review proposed and accepted knowledge-agent nodes for admission, duplicates, stale conditions and broken anchors. Use for a knowledge contribution review or a scheduled knowledge maintenance run.
---

Run `knowledge-agent review BRANCH` to compare a submission with the latest observed
accepted snapshot. Treat its duplicate list as candidates, not equivalence. Compare
scope, conclusion, conditions, versions, evidence and applicable skills. Recheck
all admission gates and relationship meaning. Resolve conflicts before admission.
A clean structural report does not establish semantic correctness.

For accepted content, run `maintain --repositories MAP.json --duplicates`; use `review-impact`
with changed paths/symbols or a code diff. Follow dependency edges when a shared
constraint changes. `related_to` is exploratory, not invalidation propagation.
Review external dependencies, configuration and deployment conditions even when
anchors are unchanged. Age, low usage, weight or orphan status do not prove decay.

Read the existing node before proposing a correction. Declare `update` for its
stable ID in the manifest's `operations` map; do not create a replacement merely
because an ID lookup fails. Resolve redirects to the survivor first.
Prepare corrections through `propose`: refresh moved anchors after inspecting code,
set uncertain claims to `needs_review`, revise scope, or preserve history with
`superseded`/`archived`. A historical reason may remain correct after its condition
changes. Merges use the manifest's retired-ID-to-survivor map and an admitted revised
survivor; review retained evidence and meaningful links. The tool redirects references
and preserves source provenance. Do not delete history to hide uncertainty.

Rerun review immediately before a merge. The report identifies the observed accepted
SHA; the host's serialized queue or merge policy must ensure it is still current.
There is no automatic merge command or authority. This skill does not grant remote
write or messaging permission. A scheduler must invoke this workflow independently
of new submissions; installing the skill alone does not schedule maintenance.
