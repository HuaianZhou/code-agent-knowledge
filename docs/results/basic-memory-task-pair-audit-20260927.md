# Basic Memory task-pair admission audit

**Decision: none of these three pairs qualifies as a strong primary positive
capture-and-reuse case. No additional agent trials were started.** All three have
authentic historical rationale and related later work, but their central claims
are already accessible in the later source tree. This is not a finding that Basic
Memory has no suitable cases, or that knowledge retrieval cannot save time.

The audit checked the earlier pre-fix tree, the earlier merged fix, and the later
pre-fix tree. Targeted searches covered source, documentation, tests, project
guidance, and skills. Positive matches were read in context. Absence from a keyword
search alone was never treated as proof that a claim was undocumented.

Exact revisions, source URLs, discussion timestamps, search patterns and evidence
hashes are in the [audit record](basic-memory-task-pair-audit-20260927.json).

## 1. MCP gateway retries → WebDAV transfer retries

**Earlier work:** investigate the failures described in
[issue #1378](https://github.com/basicmachines-co/basic-memory/issues/1378), before
fix `44e6a991`. **Later work:** repair a large Team transfer that repeatedly stops
at a rate limit, before [PR #1532](https://github.com/basicmachines-co/basic-memory/pull/1532)
(`b04d1b6d`).

**Expected knowledge:** the gateway reportedly rejects a throttled request before
application processing. That supports retrying replayable writes after that
specific rejection; it does not authorize retrying an ambiguous timeout. Preserve
the claim's reported source and scope, rather than treating it as verified behavior
of arbitrary services. The later task could use this reasoning when reviewing retry
coverage across enumeration, download, and upload.

**Novelty check:** this contract is not explained by the earlier wrappers' simple
429 error branches. However, the completed earlier fix writes it directly into
`_request_with_rate_limit_retry`. It remains plainly documented at the later task's
[baseline, lines 294–298](https://github.com/basicmachines-co/basic-memory/blob/3452c821d76c083823d020984d71e06904a1ff1e/src/basic_memory/mcp/tools/utils.py#L294).
The rationale would therefore compete with a readily discoverable code reference.

**Additional problem:** the two transports have different retry policies. Transferring
the MCP helper's exact attempt and wait limits would not itself establish a correct
WebDAV solution. Knowledge must preserve context rather than impose one global rule.

**Potential behavioral checks:** a throttled walk and transfer make progress;
retried uploads preserve body and conditional headers; create-only conflicts are
not overwritten; permanent errors remain visible; retries terminate. These would
test retry behavior, not by themselves prove that stored knowledge helped.

**Verdict:** retain as a possible navigation/cost comparison; reject as the primary
positive capture case under our current cheap-recovery admission criterion.

## 2. Team transfer authorization → cloud-client routing

**Earlier work:** Team members cannot run the documented transfer path without
owner-only storage credentials, discussed in
[PR #1263](https://github.com/basicmachines-co/basic-memory/pull/1263), before
`92f9ee67`. **Later work:** Team transfers still return 404s, addressed by
[PR #1310](https://github.com/basicmachines-co/basic-memory/pull/1310), before
`51992cc1`.

**Expected knowledge:** tenant-wide storage credentials cannot represent per-project
Team permissions. Transfers must preserve authorization through the service, and
client correctness depends on deployed server capabilities. The review discussion
also makes a real deployment dependency explicit: merging a server change is not
the same as having its conditional-write behavior deployed.

**Novelty check:** the earlier fix records the authorization rationale in the
[transfer module's opening documentation](https://github.com/basicmachines-co/basic-memory/blob/f84ea7280226118052b09f9dc184ece94b10ce46/src/basic_memory/cli/commands/cloud/webdav_transfer.py#L1).
Moreover, the existing upload path already chooses the control-plane client, and
[`test_cloud_upload_uses_control_plane_client`](https://github.com/basicmachines-co/basic-memory/blob/f84ea7280226118052b09f9dc184ece94b10ce46/tests/cli/cloud/test_upload_command_routing.py#L15)
states the routing behavior directly, even before the earlier Team-transfer fix.

**Relevance gap:** knowing why bucket credentials are inappropriate does not by itself
establish where WebDAV is mounted. The precise cloud-root diagnosis belongs to the
later investigation. Putting it into an earlier knowledge node from the later PR
would leak the answer. Earlier deployment status also must not be treated as current
without renewed evidence.

**Potential behavioral checks:** correct client/base selection; project/workspace
identity retained; no request for broadly scoped credentials; conflict behavior
preserved. A local mocked routing check cannot confirm production deployment.

**Verdict:** reject. The early rationale is documented, and the late routing answer
has an existing nearby example. Deployment facts are interesting capture material,
but this pair does not establish their incremental value for the later task.

## 3. Embedding-process memory → cross-encoder memory

**Earlier work:** investigate the long-lived process report in
[issue #872](https://github.com/basicmachines-co/basic-memory/issues/872), before
hardening fix `8acdb49a` / PR #903. **Later work:** investigate retained memory during
reranked searches, before [PR #1555](https://github.com/basicmachines-co/basic-memory/pull/1555)
(`fa306622`).

**Expected knowledge:** the reported failure concerns native allocations and model
lifetime under sustained multi-project use, not merely Python object counts. Review
provider reuse and ONNX arena behavior. The maintainer's cache-key-drift explanation
was explicitly a hypothesis; a captured node must not convert it into a proven root
cause or promise that disabling an arena immediately reduces process RSS.

**Novelty check:** before the first fix, the incident provides operational evidence
that code inspection alone cannot establish. But at the later baseline,
[`fastembed_provider.py`](https://github.com/basicmachines-co/basic-memory/blob/ba81f807ad0a7799f10c8e8022cd5622cf8f3034/src/basic_memory/repository/fastembed_provider.py#L89)
already explains the arena mitigation and links #872. A
[named regression test](https://github.com/basicmachines-co/basic-memory/blob/ba81f807ad0a7799f10c8e8022cd5622cf8f3034/tests/repository/test_fastembed_provider.py#L138)
pins the setting. The cross-encoder lives beside that provider. The reusable action
is therefore readily recoverable by inspecting the related implementation.

**Potential behavioral checks:** provider/session reuse; actual ONNX setting readback;
bounded candidate batches; every candidate scored in order; acceptable score drift.
Real memory/latency measurements would be separate. Mock construction assertions do
not prove the reported memory problem or a production improvement.

**Verdict:** reject as the primary positive case. It may be useful for measuring
cross-component discovery and uncertainty handling, but would repeat the previous
pilot's novelty problem.

## What the next eligible pair must establish

Before spending another agent run, identify a specific source-backed claim that
survives the earlier task without becoming fully explained by a nearby comment,
test, document, or existing skill, and identify a later decision it could influence.
Operational constraints and rejected design tradeoffs are leads, not automatic
qualifiers. No documentation should be removed to manufacture novelty.

For a qualifying pair, freeze the expected claim and evidence without prescribing
node wording/count. Run the earlier task with standing capture guidance only. Score
triggering, supported capture, admission, and submission separately. Then compare
fresh later-task sessions with and without the **actual reviewed capture**, keeping
ordinary source access and task conditions equal. Measure retrieval before the
relevant decision, correctness, repeated investigation, and cost. Allow both the
zero-write outcome and a successful no-knowledge baseline.

Git revisions here are immutable. Public issue/PR bodies are current retrieved
versions; creation dates do not establish that every sentence existed at that time.
Any future selected trial must freeze and audit its discussion excerpts against the
intended evidence cutoff. External gateway and production-runtime claims in this
audit remain attributed reports, not independently verified deployments.
