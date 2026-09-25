"""Evaluator-side preparation, isolated execution and artifact-based scoring.

Only input/, workspace/ and output/ enter the agent container. Gold criteria and
grading tests remain outside it. No host-execution fallback is offered.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import json
import random
import re
import shutil
import subprocess
import time
import uuid

from knowledge_agent.gitstore import git, initialize, snapshot
from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import KnowledgeError, require, resolve
from .fixtures import cases, nodes, QUERIES, write_project

ROOT = Path(__file__).resolve().parents[1]


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def init_repo(path, content):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Evaluation Fixture")
    git(path, "config", "user.email", "fixture@example.invalid")
    # Preserve the same bytes when Windows-created fixtures are mounted in Linux.
    git(path, "config", "core.autocrlf", "false")
    if not (path / "README.md").exists():
        (path / "README.md").write_text("Synthetic evaluation repository.\n", encoding="utf-8")
    for n in content.values():
        target = path / n.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(n.markdown(), encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "Seed evaluation fixture")
    return snapshot(path, "main")[0]


def fresh(path):
    path = Path(path).resolve()
    require(not path.exists(), f"output already exists: {path}; use a fresh run directory")
    path.mkdir(parents=True)
    return path


def evaluation_embedding(model=None, revision=None, diagnostic=False):
    if diagnostic:
        require(model is None and revision is None, "lexical diagnostic cannot specify a semantic model")
        return {"backend": "lexical", "model": "lexical-hash-v1", "revision": "1"}
    require(bool(model) and bool(re.fullmatch(r"[0-9a-f]{40}", revision or "")),
            "supply embedding model and immutable 40-character revision, or explicitly select lexical diagnostic")
    return {"backend": "sentence-transformers", "model": model, "revision": revision}


def prepare_capture(output, model, embedding_model=None, embedding_revision=None, lexical_diagnostic=False):
    require(bool(model), "declare the agent model/version before preparing trials")
    embedding = evaluation_embedding(embedding_model, embedding_revision, lexical_diagnostic)
    root = fresh(output)
    for case in cases():
        trial = root / case["id"]
        public, workspace = trial / "input", trial / "workspace"
        public.mkdir(parents=True)
        (public / "applicable-skills").mkdir()
        (trial / "output").mkdir()
        write_project(workspace / "project")
        code_base = init_repo(workspace / "project", {})
        code_head = code_base
        maintenance_case = case.get("kind") == "maintenance"
        if maintenance_case:
            (workspace / "project" / "writer.py").write_text(
                'from enum import Enum\nimport json\nclass State(str, Enum):\n    NEW = "new"\n    PAID = "paid"\n    CANCELLED = "cancelled"\n'
                'def append_order(stream, order_id, state):\n    stream.write(json.dumps({"id": order_id, "state": state.value, "version": 2}) + "\\n")\n', encoding="utf-8")
            (workspace / "project" / "recovery.py").write_text(
                'import json\ndef replay(stream):\n    return [(row["id"], row["state"]) for row in map(json.loads, stream)]\n', encoding="utf-8")
            git(workspace / "project", "add", ".")
            git(workspace / "project", "commit", "-m", "Use named v2 states after migration")
            code_head = git(workspace / "project", "rev-parse", "HEAD").stdout.strip()
        corpus = nodes()
        seed = {key: corpus[key] for key in case["seed"]}
        for n in seed.values():
            n.meta["anchors"] = [{"repo": "orders", "path": "writer.py", "role": "affected_code", "verified_commit": code_base}]
        base = init_repo(workspace / "knowledge", seed)
        dump(workspace / "config.json", {
            "repo": "/workspace/knowledge", "branch": "main", "state": "/workspace/state",
            "embedding": embedding,
            "provider": None, "automatic_merge": False})
        shutil.copytree(ROOT / "knowledge_agent", public / "tool-source" / "knowledge_agent",
                        ignore=shutil.ignore_patterns("__pycache__"))
        skill_name = "knowledge-maintain" if maintenance_case else "knowledge-extract"
        shutil.copytree(ROOT / "skills" / skill_name, public / "skills" / skill_name)
        dump(public / "repositories.json", {"orders": "/workspace/project"})
        if case["skills"]:
            skill = public / "applicable-skills" / "encoding-verification" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: encoding-verification\ndescription: Verify order encoding edits.\n---\n"
                             "Whenever order encoding changes, run compatibility tests before completion.\n", encoding="utf-8")
        dump(public / "request.json", {
            "task": f"Execute the {skill_name} skill on the supplied conversation and actual project/skill evidence. "
                    "Prepare proposals only: leave them for a separate reviewer; do not accept them. Run the CLI, not merely describe a plan.",
            "conversation": case["conversation"], "project": "/workspace/project",
            "model": model, "max_output_tokens": 8000,
            "skill": f"/input/skills/{skill_name}/SKILL.md", "applicable_skills": "/input/applicable-skills",
            "repositories": "/input/repositories.json", "code_base": code_base, "code_head": code_head,
            "cli": "python -m knowledge_agent --config /workspace/config.json",
            "result_contract": {"outcome": "zero_qualifying_candidates or proposal", "proposal_branch": "branch if committed, otherwise null"},
            "evidence": "Return raw tool-call trace and actual task-end result; do not infer success from narrative alone."})
        dump(trial / "private.json", {"kind": "capture", "case": case, "base_revision": base,
                                     "fixture_kind": "synthetic", "model": model, "embedding": embedding,
                                     "tool_revision": git(ROOT, "rev-parse", "HEAD").stdout.strip()})
    dump(root / "suite.json", {"kind": "capture", "cases": [c["id"] for c in cases()],
                              "embedding": embedding, "status": "prepared_not_run"})
    return {"directory": str(root), "cases": len(cases()), "status": "prepared_not_run"}


def container_command(trial, image, *, grading=False, network="none", env_file=None, codex_auth=None):
    trial = Path(trial).resolve()
    require(bool(image) and not image.startswith("-"), "provide an agent/grade image")
    require(network in ("none", "bridge"), "network must be none or bridge")
    cmd = ["docker", "run", "--rm", "--pull=never", "--read-only", "--cap-drop=ALL",
           "--security-opt=no-new-privileges", "--pids-limit=128", "--memory=4g", "--cpus=2",
           "--network=" + ("none" if grading else network), "--tmpfs", "/tmp:rw,nosuid,size=512m"]
    mounts = [(trial / "workspace", "/workspace", grading)]
    mounts += [(trial / "grading", "/grading", True)] if grading else [
        (trial / "input", "/input", True), (trial / "output", "/output", False)]
    for source, destination, readonly in mounts:
        require(source.is_dir() and not source.is_symlink(), f"invalid mount: {source}")
        require("," not in str(source), "Docker mount paths must not contain commas")
        cmd += ["--mount", f"type=bind,source={source},target={destination}" + (",readonly" if readonly else "")]
    if grading:
        return cmd + ["--entrypoint", "python", image, "-B", "/grading/check.py"]
    if codex_auth:
        auth = Path(codex_auth).resolve()
        require(auth.is_file() and not auth.is_symlink() and "," not in str(auth), "invalid Codex auth file")
        cmd += ["--mount", f"type=bind,source={auth},target=/run/codex-auth.json,readonly"]
    if env_file:
        cmd += ["--env-file", str(Path(env_file).resolve())]
    return cmd + ["--workdir", "/workspace/project", "--env", "PYTHONPATH=/input/tool-source", image,
                  "--request", "/input/request.json", "--output", "/output/result.json"]


def run_trial(trial, image, timeout=600, network="none", env_file=None, grading=False, codex_auth=None):
    require(shutil.which("docker") is not None, "Docker is required for isolated agent runs; no host fallback is allowed")
    require(timeout > 0, "timeout must be positive")
    trial = Path(trial).resolve()
    record = trial / ("grading-run.json" if grading else "run.json")
    require(not record.exists(), "trial already executed; prepare a fresh workspace/session for each run")
    # Resolve the local immutable image ID and record it; never silently pull latest.
    inspect = subprocess.run(["docker", "image", "inspect", "--format={{.Id}}", image], capture_output=True, text=True)
    require(inspect.returncode == 0, "image is not available locally; build/pull it explicitly first")
    image_id = inspect.stdout.strip()
    cmd = container_command(trial, image_id, grading=grading, network=network, env_file=env_file, codex_auth=codex_auth)
    container_name = "knowledge-eval-" + uuid.uuid4().hex
    cmd[2:2] = ["--name", container_name]
    started = time.monotonic()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        cleanup = subprocess.run(["docker", "rm", "--force", container_name], capture_output=True, text=True)
        exit_code, stdout, stderr = 124, "", "Agent exceeded the wall-time budget."
        if cleanup.returncode:
            stderr += f" Container cleanup failed; inspect {container_name}."
    (trial / ("grading.stdout.txt" if grading else "agent.stdout.txt")).write_text(stdout, encoding="utf-8")
    (trial / ("grading.stderr.txt" if grading else "agent.stderr.txt")).write_text(stderr, encoding="utf-8")
    report = {"image_id": image_id, "exit_code": exit_code, "wall_seconds": time.monotonic() - started,
              "isolation": "docker-scoped-mounts", "network": "none" if grading else network,
              "status": "completed" if exit_code == 0 else "failed"}
    dump(record, report)
    return report


def _pack(records, budget):
    selected, used = [], 0
    for record in records:
        size = len(json.dumps(record, ensure_ascii=False).encode("utf-8"))
        if size + used <= budget:
            selected.append(record)
            used += size
    return {"results": selected, "estimated_tokens": used, "truncated": len(selected) < len(records),
            "token_estimator": "conservative UTF-8 bytes of returned node records"}


def controlled_contexts(index, embedder, budget):
    require(budget > 0, "context budget must be positive")
    view = index.view()
    ranked = index.search(view, "order lifecycle feature implementation", embedder,
                          limit=max(1, len(view.nodes)), candidates=max(1, len(view.nodes)))["results"]
    empty = _pack([], budget)
    if not ranked:
        return {"none": empty, "flat": empty, "graph": empty}, None
    seed = ranked[0]["metadata"]["id"]
    # Flat and graph share the same entry retrieval; both account for complete node records.
    records = [{**view.nodes[row["metadata"]["id"]].as_dict(), "relationship_path": []} for row in ranked]
    require(len(json.dumps(records[0], ensure_ascii=False).encode("utf-8")) <= budget,
            "context budget cannot fit the shared entry node; increase it before comparing conditions")
    flat = _pack(records, budget)
    graph = view.context(seed, depth=2, max_nodes=max(1, len(view.nodes)), max_tokens=budget)
    return {"none": empty, "flat": flat, "graph": graph}, seed


GRADE = '''import io, json, sys, unittest
sys.path.insert(0, "/workspace/project")
from writer import State, append_order
from recovery import replay

class BehavioralChecks(unittest.TestCase):
    def test_retained_meanings(self):
        self.assertEqual((int(State.NEW), int(State.PAID), int(State.CANCELLED)), (0, 1, 2))
    def test_old_records(self):
        stream = io.StringIO('{"id":"old","state":2}\\n')
        self.assertEqual(replay(stream), [("old", "cancelled")])
    def test_new_feature(self):
        stream = io.StringIO()
        append_order(stream, "refund", State.REFUNDED)
        stream.seek(0)
        self.assertEqual(replay(stream), [("refund", "refunded")])

if __name__ == "__main__":
    unittest.main()
'''


def prepare_reuse(output, model, repeats=3, seed=42, budget=2400, capture_trial=None,
                  embedding_model=None, embedding_revision=None, lexical_diagnostic=False):
    require(bool(model) and repeats > 0, "supply model/version identifier and positive repeat count")
    embedding = evaluation_embedding(embedding_model, embedding_revision, lexical_diagnostic)
    root = fresh(output)
    provenance = "curated_fixture"
    corpus = nodes()
    capture_source = None
    if capture_trial:
        source = Path(capture_trial).resolve()
        result = read(source / "output" / "result.json")
        if result.get("outcome") == "zero_qualifying_candidates":
            corpus = {}
        else:
            branch = result.get("proposal_branch", "")
            require(branch.startswith("knowledge/"), "capture source has no proposal branch")
            rev, corpus, _ = snapshot(source / "workspace" / "knowledge", branch)
            capture_source = {"trial": str(source), "revision": rev}
        provenance = "raw_capture"
    repo = root / "evaluator-knowledge"
    knowledge_revision = init_repo(repo, corpus)
    embedder = Embedder(embedding)
    index = Index(root / "evaluator-index")
    index.rebuild(repo, "main", embedder)
    contexts, entry = controlled_contexts(index, embedder, budget)
    trials = []
    for repeat in range(repeats):
        for condition in ("none", "flat", "graph"):
            trial_id = f"repeat-{repeat + 1}-{condition}"
            trial = root / trial_id
            (trial / "input").mkdir(parents=True)
            (trial / "output").mkdir()
            write_project(trial / "workspace" / "project")
            context = contexts[condition]
            dump(trial / "input" / "knowledge.json", context)
            request = {"task": "Add a REFUNDED order state and support writing and replaying it. Keep existing public APIs usable. Run relevant tests.",
                       "project": "/workspace/project", "knowledge": "/input/knowledge.json",
                       "model": model, "max_output_tokens": 8000,
                       "result_contract": {"model": "actual model/version", "tokens_input": "number or null",
                                           "tokens_output": "number or null", "tool_calls": "number or null",
                                           "human_corrections": "number or null"},
                       "trace": "Save raw tool-call and decision trace to /output/trace.jsonl. Do not access the evaluator."}
            dump(trial / "input" / "request.json", request)
            (trial / "grading").mkdir()
            (trial / "grading" / "check.py").write_text(GRADE, encoding="utf-8")
            hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (trial / "workspace" / "project").iterdir()}
            dump(trial / "private.json", {"kind": "reuse", "condition": condition, "repeat": repeat + 1,
                  "knowledge_provenance": provenance, "knowledge_revision": knowledge_revision,
                  "model": model, "context_budget": budget, "context_used": context["estimated_tokens"],
                  "entry_id": entry if condition != "none" else None, "starting_files": hashes})
            trials.append(trial_id)
    random.Random(seed).shuffle(trials)
    experiment = {"kind": "controlled_reuse", "fixture_kind": "synthetic", "knowledge_provenance": provenance,
                  "capture_source": capture_source, "model": model, "seed": seed, "repeats": repeats,
                  "context_budget": budget, "retrieval_backend": embedding["backend"], "embedding": embedding, "run_order": trials,
                  "pass_criteria": {"behavior": "all grader checks pass", "quality": "independent trace review required",
                                    "adoption": "not established by this small synthetic experiment"},
                  "status": "prepared_not_run",
                  "limitation": "Retrieval is supplied under controlled budgets to isolate graph expansion. This is not a test of autonomous retrieval invocation."}
    dump(root / "experiment.json", experiment)
    return experiment


def summarize_reuse(root):
    root = Path(root).resolve()
    experiment = read(root / "experiment.json")
    rows = []
    for trial_id in experiment["run_order"]:
        trial = root / trial_id
        private = read(trial / "private.json")
        execution = read(trial / "run.json") if (trial / "run.json").exists() else None
        grade = read(trial / "grading-run.json") if (trial / "grading-run.json").exists() else None
        result = read(trial / "output" / "result.json") if (trial / "output" / "result.json").exists() else {}
        status = "pending" if execution is None else "needs_grading" if grade is None else "passed" if grade["exit_code"] == 0 else "failed"
        if execution and (execution["exit_code"] != 0 or result.get("model") != experiment["model"]):
            status = "invalid_run"
        rows.append({"trial": trial_id, "condition": private["condition"], "status": status,
                     "wall_seconds": execution["wall_seconds"] if execution else None,
                     "context_used": private["context_used"],
                     "adapter_reported_metrics": {k: result.get(k) for k in ("tokens_input", "tokens_output", "tool_calls", "human_corrections")}})
    report = {"experiment": experiment, "trials": rows, "adoption_conclusion": None,
              "note": "Grader results measure behavior. Metrics/trace require independent review; agent claims alone never establish correctness."}
    dump(root / "summary.json", report)
    return report


def score_capture(trial, scorecard=None):
    trial = Path(trial).resolve()
    private = read(trial / "private.json")
    require(private["kind"] == "capture", "not a capture trial")
    case, base = private["case"], private["base_revision"]
    result = read(trial / "output" / "result.json")
    repo = trial / "workspace" / "knowledge"
    _, before, _ = snapshot(repo, base)
    errors = []
    require(snapshot(repo, "main")[0] == base, "capture changed accepted main instead of leaving a proposal")
    dirty = git(repo, "-c", "core.fsmonitor=false", "diff", "--no-ext-diff", "--no-textconv", "--name-only", base,
                "--", "nodes", "aliases.json").stdout.strip()
    untracked = git(repo, "-c", "core.fsmonitor=false", "ls-files", "--others", "--exclude-standard", "--", "nodes").stdout.strip()
    if dirty or untracked:
        errors.append("capture wrote directly into accepted knowledge checkout")
    if result.get("outcome") == "zero_qualifying_candidates":
        branches = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads/knowledge/").stdout.strip()
        if branches:
            errors.append("zero-write result left contribution branches")
        changed = {}
    else:
        branch = result.get("proposal_branch", "")
        require(result.get("outcome") == "proposal" and branch.startswith("knowledge/"), "missing actual proposal result")
        _, proposed, _ = snapshot(repo, branch)
        if set(before) - set(proposed):
            errors.append("capture unexpectedly deleted existing nodes")
        changed = {key: n for key, n in proposed.items() if key not in before or n.markdown() != before[key].markdown()}
    expected = case["expected"]
    if not expected["min_changes"] <= len(changed) <= expected["max_changes"]:
        errors.append("changed-node count violates scenario contract")
    if "allowed_changed_ids" in expected and set(changed) - set(expected["allowed_changed_ids"]):
        errors.append("paraphrase produced a new identity instead of reusing the existing claim")
    if set(expected.get("required_changed_ids", [])) - set(changed):
        errors.append("changed condition did not revise the affected existing constraint")
    if expected.get("forbid_verified") and any(n.meta["evidence_state"] == "verified" for n in changed.values()):
        errors.append("unverified evidence was promoted to verified")
    if expected.get("required_target") and not any(r["target"] == expected["required_target"]
            for n in changed.values() for r in n.meta["relations"]):
        errors.append("shared constraint was not reused through a meaningful relationship")
    semantic = read(Path(scorecard)) if scorecard else None
    required = ("admission", "evidence", "reuse", "relationships", "scope")
    if semantic:
        require(bool(semantic.get("reviewer")) and all(isinstance(semantic.get(k), dict) and
                type(semantic[k].get("passes")) is bool and bool(semantic[k].get("evidence")) for k in required),
                "scorecard needs reviewer and passes/evidence judgments for every criterion")
    run = read(trial / "run.json") if (trial / "run.json").exists() else None
    if run and result.get("model") != private["model"]:
        errors.append("adapter model declaration does not match the predeclared model")
    status = "failed" if errors else "needs_semantic_review"
    if semantic:
        status = "passed" if not errors and all(semantic[k]["passes"] for k in required) else "failed"
    if not run or run["exit_code"] != 0:
        status = "unverified_run"
    report = {"case": case["id"], "status": status, "contract_errors": errors,
              "changed_ids": sorted(changed), "raw_proposals": [n.as_dict() for n in changed.values()],
              "semantic_scorecard": semantic, "rubric": case["rubric"], "execution": run,
              "note": "Artifact checks are not semantic judgment; self-reported success is not a pass."}
    dump(trial / "capture-score.json", report)
    return report


def retrieval_report(index, view, embedder, k=3, threshold=.8, require_semantic=True):
    require(0 < k < len(view.nodes), "K must be positive and smaller than the corpus")
    require(0 <= threshold <= 1, "recall threshold must be in [0,1]")
    if require_semantic:
        require(embedder.semantic, "lexical embeddings cannot pass semantic evaluation")
    rows = []
    for target, query in QUERIES:
        require(target in view.nodes, "retrieval corpus missing a target")
        require(view.nodes[target].meta["title"].lower() not in query.lower(), "query repeats target title")
        found = index.search(view, query, embedder, limit=k, candidates=max(k, 50))["results"]
        ids = [r["metadata"]["id"] for r in found]
        rows.append({"query": query, "target": target, "returned_ids": ids,
                     "rank": ids.index(target) + 1 if target in ids else None})
    recall = sum(r["rank"] is not None for r in rows) / len(rows)
    return {"kind": "semantic" if embedder.semantic else "lexical_diagnostic", "k": k,
            "recall_at_k": recall, "mrr_at_k": sum(1 / r["rank"] if r["rank"] else 0 for r in rows) / len(rows),
            "threshold": threshold, "passed": recall >= threshold if embedder.semantic else None,
            "embedding": view.signature, "knowledge_revision": view.revision, "queries": rows}


def semantic_eval(output, model=None, revision=None, k=3, threshold=.8, diagnostic=False):
    if not diagnostic:
        require(bool(model) and bool(re.fullmatch(r"[0-9a-f]{40}", revision or "")), "semantic test requires model and immutable 40-character model revision")
    root = fresh(output)
    repo = root / "knowledge"
    init_repo(repo, nodes())
    config = {"backend": "lexical" if diagnostic else "sentence-transformers",
              "model": "lexical-hash-v1" if diagnostic else model, "revision": "1" if diagnostic else revision}
    embedder = Embedder(config)
    index = Index(root / "index")
    index.rebuild(repo, "main", embedder)
    report = retrieval_report(index, index.view(), embedder, k, threshold, not diagnostic)
    dump(root / "retrieval-report.json", report)
    return report
