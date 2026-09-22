# Validation record

Local validation on Windows, Python 3.12, Git 2.53, PyYAML 6.0.3 and sqlite-vec 0.1.9:

- Editable package build/install and CLI entry point work.
- Integration tests exercise real temporary Git repositories and sqlite-vec, not
  mocked repository/index operations.
- Complete local demo passed: isolated proposal → review → explicit fixture
  acceptance → bare-remote sync → separate reader → A → B ← C → rename impact.
- Zero-candidate demo produces zero writes. Both skill frontmatters validated.
- Failure injection demonstrated index rollback; simultaneous writers produced
  coherent snapshots. Offline-sync regression retains the last accepted revision.

Not executed: an approved transformer model download/inference, hosted GitHub/GitLab
requests, scheduled agent execution, autonomous extraction, or controlled fresh-agent
behavioral evaluation. These results establish local mechanics, not adoption value.

Local setup and acceptance coverage: new repository/config/index creation, repeatable
setup, preservation of existing directories, no-remote synchronization, explicit
reviewed-commit acceptance and index refresh, stale/concurrent review rejection,
dirty-checkout preservation, acceptance locking and remote-workflow separation.
All 33 automated tests passed after this change. The Windows `install.ps1` script
built and installed the wheel, created a separate demo knowledge repository and
index, and the installed CLI was checked from outside the source root.

The capture and maintenance skills were refactored into executable workflows.
Both passed skill validation. Their command sequences were exercised on local,
hand-authored fixtures: zero-write capture, schema validation, create/update proposals,
review, local acceptance, retrieval, anchor lookup, maintenance and impact inspection.
This checks command compatibility, not autonomous agent judgment or capture quality.

## Three-layer evaluation implementation

On 2026-09-21, all 44 automated tests passed (69 seconds). Added tests cover
cross-repository anchor isolation, combined filters and ordering, incremental/full
index equivalence, local/remote proposal visibility, evaluator isolation boundaries,
artifact-based scoring, and hidden-grader calibration against compatible and broken
fixture implementations.

The evaluation CLI prepared eight capture/maintenance scenarios and nine reuse
trials (three conditions, three repeats). These are explicitly `prepared_not_run`,
with model `not-configured`; preparing fixtures is not an agent evaluation.
The offline lexical diagnostic returned Recall@3 = 0.9 and MRR@3 = 0.7333 over ten
queries. Its `passed` field is null: this does not establish semantic retrieval.

Docker and the optional embedding backend are unavailable in this environment.
Real isolated agent runs, independent capture scorecards, transformer inference,
and real-project adoption measurements remain pending. See [the executable
evaluation guide](evaluation.md) and [coverage map](evaluation-coverage.md).

## Semantic retrieval run, 2026-09-22

Installed Sentence Transformers 5.7.0 and Torch 2.14.0 in the project environment.
Ran actual model inference and SQLite cosine search with
`sentence-transformers/all-MiniLM-L6-v2` pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (384 dimensions).
All ten queries returned their target at rank 1: Recall@3 = 1.0, MRR@3 = 1.0,
passing the predeclared 0.8 Recall@3 threshold. The full
[machine-readable result](results/semantic-minilm-20260922.json) records every query.
This is a small synthetic retrieval test, not an agent-capture evaluation.

All 46 automated tool/harness checks passed. The two new checks verify semantic
setup configuration preservation and mandatory explicit embedding selection in
capture preparation. Fresh eight-case capture and nine-trial reuse suites use
the same pinned semantic model. They remain prepared, not agent-executed.
