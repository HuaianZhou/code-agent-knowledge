# Basic Memory historical pilot

This pilot evaluates an ordinary coding task with the installed standing capture
policy. The task request does not name capture, the skill, or the knowledge CLI.
The original Basic Memory AGENTS.md and project skills remain available. Our policy
is appended without replacing them. This tests standing-policy compliance, not
skill-description-only discovery or a guaranteed completion hook.

## Frozen investigation

- Upstream: <https://github.com/basicmachines-co/basic-memory>
- Source: `60408ad7d53e4ec448abaf04d0bfa222aa2f8e78`.
- Incident: <https://github.com/basicmachines-co/basic-memory/issues/1159>.
- Model: `gpt-6-astra`, fresh isolated session, 1,200-second wall limit.
- Embeddings: the existing pinned MiniLM model; no lexical substitution.
- Input: historical source plus a short, attributed incident paraphrase. It gives
  symptoms and the asynchronous-acceptance constraint, but omits the suggested fix
  and subsequent issues. No invented developer conversation is supplied.
- Task: reproduce and fix background indexing of a note whose file is not yet
  materialized, preserving asynchronous acceptance and genuine missing-file errors.
- Knowledge starts empty; the actor may propose nodes or submit zero candidates.
  An absent submission is distinct from an explicit zero-candidate decision.

The actor sees an archive of the historical tree in a fresh repository, not a clone
containing future commits. Network is available for the model service; the task
prohibits consulting external history. Trace review must flag external solution
access. This restriction is not enforced by an outbound domain firewall, and model
familiarity with public history cannot be ruled out.

## Separate checks

1. Confirm the historical environment runs relevant existing SQLite tests.
2. Calibrate a held-out behavioral regression from upstream fix
   `fe5f2e793535a02a8532317dd79a3162a968bef0`: it must fail on the original snapshot
   for the reported failure and pass on the reference fix.
3. Run the actor without follow-up capture reminders or evaluator intervention.
4. Grade its code using the same held-out test in a network-disabled container.
   The grader checks actual SQLite graph/search behavior through the local runtime;
   it does not require the upstream patch. It is one regression, not exhaustive
   equivalence or performance validation.
5. Review native commands and actual Git proposals. Check admission, evidence,
   overlap with existing docs/skills, scope, anchors, and future action. Do not
   accept the actor's narrative as proof or force a number of nodes.
6. Only reviewed knowledge may enter a subsequent reuse experiment. Preserve raw
   proposals and record acceptance or rejection separately. Zero useful knowledge
   is a valid result; do not insert evaluator-written replacements.

## Reproduction

From this repository, with the existing evaluation base image and Python environment:

```powershell
git clone https://github.com/basicmachines-co/basic-memory.git .demo/basic-memory-source
python -m evaluation.basic_memory .demo/basic-memory-run --source .demo/basic-memory-source
docker build -t knowledge-eval-basic-memory:local .demo/basic-memory-run/build
python -m evaluation run .demo/basic-memory-run/calibration-before --image knowledge-eval-basic-memory:local --grade
python -m evaluation run .demo/basic-memory-run/calibration-reference --image knowledge-eval-basic-memory:local --grade
python -m evaluation run .demo/basic-memory-run/investigation --image knowledge-eval-basic-memory:local --network bridge --env-file ENV_FILE --codex-auth AUTH_FILE --timeout 1200
python -m evaluation run .demo/basic-memory-run/investigation --image knowledge-eval-basic-memory:local --grade
```

The Docker build uses the historical dependency lock in a separate Python
environment. The knowledge CLI uses the existing global runtime and cached
embedding model. No private grader, source-history clone, host home, or Docker
socket is mounted into the actor.

Preparation supplies `evaluation/basic_memory_grade.py` with a private `upstream_regression.py` copied
from `tests/index/test_local_project_index.py` at the reference fix and placed next
to `grading/check.py`. It runs
`test_local_relation_resolution_refreshes_pending_source_without_markdown_file`
on a temporary copy of the actor's source. Upstream test material stays under the
ignored evaluation output; its revision and AGPL license provenance are recorded.

## Follow-up design

The candidate follow-up is the search-refresh retry incident
<https://github.com/basicmachines-co/basic-memory/issues/1163>. Use an appropriate
pre-fix revision and fresh sessions with identical task wording, code, documentation,
model, runtime and budget. Compare no knowledge with on-demand retrieval of the
reviewed capture. Do not put this incident's diagnosis or solution into the earlier
capture. Compare correctness, repeat investigation and measured cost; an equally
successful baseline is valid. A graph-only benefit requires a further comparison
and a corpus whose relationships actually distinguish the supplied evidence.
