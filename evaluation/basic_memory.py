"""Prepare a historical Basic Memory investigation with standing-policy capture."""
import argparse
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import tarfile

from .fulfillment import EMBEDDING, MODEL
from .harness import ROOT, dump, fresh, init_repo

BASE = "60408ad7d53e4ec448abaf04d0bfa222aa2f8e78"
REFERENCE = "fe5f2e793535a02a8532317dd79a3162a968bef0"
UPSTREAM = "https://github.com/basicmachines-co/basic-memory"
TASK = (
    "Investigate and fix a background indexing failure during bursty note writes. "
    "A write is acknowledged successfully, but a later relation-resolution pass can "
    "raise FileNotFoundError before the note's Markdown file appears. The note eventually "
    "becomes searchable. Reproduce the problem, implement a focused fix, and run relevant "
    "SQLite tests. Preserve asynchronous write acknowledgement and ensure genuinely missing "
    "files remain diagnosable. Explain the cause, tradeoffs, and verification. "
    "Use only this historical source snapshot and the supplied incident brief; do not "
    "consult external repository history or later solutions."
)
BRIEF = """# Historical incident brief

Source: https://github.com/basicmachines-co/basic-memory/issues/1159
Reported against commit 60408ad7d53e4ec448abaf04d0bfa222aa2f8e78.
This is an evaluator paraphrase of the report, not a fabricated developer conversation.

The reporter observed transient background FileNotFoundError failures under bursty
write load although caller-visible writes succeeded and notes eventually became
searchable. The maintainer explicitly wanted fast durable acceptance to remain
asynchronous: waiting for Markdown materialization on the request path would undo
the intended performance tradeoff. File and search projections may catch up later.
An actually missing synchronized file must still be reported as an inconsistency.

The cause and implementation must be established from the supplied source and tests.
The later fix, suggested implementation, and subsequent incidents are not supplied.
"""


def export_snapshot(source, destination, revision=BASE):
    """Archive only a pinned tree: no future Git objects enter the actor workspace."""
    archive = subprocess.run(
        ["git", "-C", str(source), "archive", revision], check=True, capture_output=True
    ).stdout
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(destination, filter="data")


def prepare_grading(root, source):
    regression_path = "tests/index/test_local_project_index.py"
    regression = subprocess.run(
        ["git", "-C", str(source), "show", REFERENCE + ":" + regression_path],
        check=True, capture_output=True,
    ).stdout
    for case, revision in (("calibration-before", BASE), ("calibration-reference", REFERENCE),
                           ("investigation", None)):
        trial = root / case
        if revision:
            export_snapshot(source, trial / "workspace/project", revision)
        grading = trial / "grading"
        grading.mkdir()
        (grading / "upstream_regression.py").write_bytes(regression)
        shutil.copyfile(ROOT / "evaluation/basic_memory_grade.py", grading / "check.py")
        dump(grading / "provenance.json", {
            "upstream": UPSTREAM, "regression_revision": REFERENCE,
            "path": regression_path, "license": "AGPL-3.0-or-later",
            "sha256": hashlib.sha256(regression).hexdigest(),
            "purpose": "held-out upstream regression, never actor-visible",
        })


def prepare(output, source):
    root = fresh(output)
    trial = root / "investigation"
    project = trial / "workspace/project"
    export_snapshot(source, project)
    public = trial / "input"
    public.mkdir(parents=True)
    (trial / "output").mkdir()
    for name in ("knowledge-extract",):
        shutil.copytree(ROOT / "skills" / name, public / "skills" / name)
    shutil.copytree(ROOT / "knowledge_agent", public / "tool-source/knowledge_agent",
                    ignore=shutil.ignore_patterns("__pycache__"))
    dump(public / "repositories.json", {"basic-memory": "/workspace/project"})
    (public / "incident.md").write_text(BRIEF, encoding="utf-8")
    policy = (ROOT / "integrations/codex/AGENTS.fragment.md").read_text(encoding="utf-8")
    policy = policy.replace("{{SKILL_PATH}}", "/input/skills/knowledge-extract/SKILL.md").replace(
        "{{CLI_COMMAND}}", "/usr/local/bin/python -m knowledge_agent --config /workspace/config.json"
    ).replace("{{REPOSITORIES_PATH}}", "/input/repositories.json")
    with (project / "AGENTS.md").open("a", encoding="utf-8") as stream:
        stream.write("\n\n" + policy)
    code_base = init_repo(project, {})
    knowledge_base = init_repo(trial / "workspace/knowledge", {})
    dump(trial / "workspace/config.json", {
        "repo": "/workspace/knowledge", "branch": "main", "state": "/workspace/state",
        "embedding": EMBEDDING, "provider": None, "automatic_merge": False,
    })
    dump(public / "request.json", {
        "task": TASK, "incident": "/input/incident.md", "project": "/workspace/project",
        "model": MODEL, "max_output_tokens": 8000,
        "test_environment": "Dependencies are installed in /opt/basic-memory/bin/python. Use that interpreter for pytest. The source checkout is on pytest's configured Python path.",
    })
    dump(trial / "private.json", {
        "case": "basic_memory_pending_materialization", "base_revision": knowledge_base,
        "code_base": code_base, "upstream": UPSTREAM, "upstream_revision": BASE,
        "trigger": "standing_AGENTS_policy", "policy_sha256": hashlib.sha256(policy.encode()).hexdigest(),
        "criteria": [
            "Reproduce pending-file failure and verify a fix without blocking acceptance",
            "Preserve visibility of genuine synchronized-file errors",
            "Inspect native trace for skill reading, admission, search and submission",
            "Review captured claims for evidence, nonduplication, scope and future action",
            "No fixed node count; zero writes and missed capture are distinct outcomes",
            "No later issue or patch access; report any contamination",
        ],
    })
    build = root / "build"
    build.mkdir()
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(project / name, build / name)
    shutil.copyfile(ROOT / "evaluation/Dockerfile.basic-memory", build / "Dockerfile")
    dump(root / "experiment.json", {
        "model": MODEL, "run_order": ["investigation"], "upstream_revision": BASE,
        "trigger": "standing_AGENTS_policy_without_task_reminder", "status": "prepared_not_run",
        "request_sha256": hashlib.sha256((public / "request.json").read_bytes()).hexdigest(),
        "limitations": ["Single historical task; no reliability estimate", "Standing policy, not description-only discovery",
                        "Public historical material may be familiar to the model", "Reuse remains a separate experiment"],
    })
    prepare_grading(root, source)
    return str(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    print(prepare(args.output, args.source))
