# Fulfillment lifecycle results, September 23–24, 2026

This is an actual Astra pilot using a synthetic fulfillment service, not a real
customer project. See the [frozen protocol and reproduction instructions](../fulfillment-evaluation.md),
[fixture code](../../evaluation/projects/fulfillment), and
[machine-readable results](fulfillment-astra-20260924.json).

## Capture and reuse

Astra first removed eager materialization from the batch exporter and added a
streaming/output-preservation test. It then executed the capture skill against an
empty knowledge repository using the supplied Operations F-17/F-18 handoffs.
The separate Codex evaluator reviewed and accepted three actual proposed nodes
without editing them: one receiver constraint and two path-specific decisions,
each linked to that constraint by `constrained_by`.

The site-specific deployment facts were labeled reported, with explicit
invalidation conditions. The nodes distinguish tested encoder behavior from
unverified external deployment facts. This was guided capture: the handoff
explicitly described the shared obligation and invited supported relationships.

Each coding cell below is one fresh Astra session with the frozen source baseline.
Pass/fail comes from the separate consumer grader, not agent self-report.

| Task | No knowledge | Semantic retrieval | Semantic + graph |
|---|---|---|---|
| Modernize normal export | Fail | Pass | Pass |
| Modernize recovery export | Fail | Pass | Pass |
| Fix inventory totals | Pass | Pass | Pass |

Both no-knowledge agents implemented the requested default but left deployment
exception mappings empty and explicitly reported missing deployment information.
Their local tests passed; north's independent consumer rejected their JSONL output.
Knowledge-enabled runs preserved north's CSV exception and passed. All inventory
runs made the correct sum change and passed the unchanged-export checks.

This demonstrates transfer of the supplied operational knowledge through capture,
review, acceptance and retrieval in this fixture. It is not a general success-rate
estimate or evidence that the baseline agents reasoned poorly: they lacked the
deployment information and correctly acknowledged that gap.

## Graph interpretation

For export and recovery, flat retrieval and graph expansion supplied the same
two node IDs: the receiver constraint and normal-export decision. The recovery
decision did not fit the 6,000-byte budget. The central constraint already included
the shared receiver fact, enough to solve both tasks. Both flat and graph export
agents also aligned recovery routing, so that behavior cannot be attributed to
graph expansion. No incremental coding benefit from the graph was established.

Maintenance did use incoming dependency edges to identify both dependent decisions,
but there was no maintenance-without-graph comparison. That validates execution of
the dependency workflow, not comparative maintenance efficiency.

## Maintenance comparison

Operations F-29 changed the reported north contract to JSONL-only while source
files remained unchanged. Original code history was imported into the maintenance
checkout so captured anchors resolved; the anchor scan then returned no findings.
Astra nevertheless inspected the external change and used `review-impact` plus
graph context to examine the shared constraint and both dependents.

It proposed updates to all three stable IDs, preserved the two dependency edges
and F-17/F-18 historical rationale, added F-29 provenance, and retained reported
evidence rather than claiming independently verified deployment. The separate
evaluator accepted these proposals unchanged.

| Knowledge supplied after migration | Normal export | Recovery export |
|---|---|---|
| Stale captured nodes | Fail | Fail |
| Reviewed maintenance output | Pass | Pass |

Both stale-knowledge coding runs failed the migrated receiver: they followed the
former CSV advice. Both maintained-knowledge runs produced JSONL v2 for north,
preserved explicit format overrides and reconstruction behavior, and passed the
independent consumer checks. Their traces explicitly distinguish F-29's current
guidance from the old exception. This demonstrates that correcting the stored
guidance affected behavior in this fixture, not just Markdown content.

## Execution and limits

All trials used the same configured `gpt-6-astra` alias, Codex CLI runtime image
`sha256:6728f3c183264eb0aff9bd202c46bcc418e3d0e75a2467dc40f2a006e29d0091`, and
MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Forty-eight automated tests passed, including grader calibration: plausible
implementations passed public tests but consumer acceptance reversed when the
external contract reversed.

Six initial coding cells completed before an Astra usage limit interrupted the
seventh. The interrupted attempt remains recorded; three remaining cells used
fresh workspaces after reset, with identical starting hashes and context contents.
No completed behavioral failure was discarded. Actual code diffs, native usage,
contexts, trace hashes, reviews and acceptance commits accompany the machine report.
Fifteen Astra sessions completed: capture, nine initial coding comparisons,
maintenance, and four post-migration comparisons. The additional quota-interrupted
attempt is retained separately. The original two never-started preparations are
marked unused because their replacement trials completed after reset.

There is one execution per cell, controlled injected retrieval, synthetic
operational evidence and Codex review rather than blind human review. No measured
real-project productivity claim follows. Post-maintenance nodes became longer;
the fixed budget fits only the constraint for export and only the recovery decision
for recovery, with graph expansion truncated. Node verbosity and context budgeting
therefore remain useful areas for further evaluation. Trials and raw traces stay
under local `.demo/fulfillment-*` directories; fixture and reports are versioned.
