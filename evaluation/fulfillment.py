"""Reproducible lifecycle pilot. Private graders never enter agent inputs.

python -m evaluation.fulfillment capture OUTPUT
python -m evaluation.fulfillment reuse OUTPUT --source ACCEPTED_KNOWLEDGE_REPO
python -m evaluation.fulfillment maintain OUTPUT --source ACCEPTED_KNOWLEDGE_REPO
python -m evaluation.fulfillment reuse OUTPUT --source ACCEPTED_KNOWLEDGE_REPO --era after
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil

from knowledge_agent.gitstore import git, snapshot
from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import require
from .harness import ROOT, dump, fresh, init_repo, read, _pack

PROJECT = Path(__file__).with_name("projects") / "fulfillment"
EMBEDDING = {"backend": "sentence-transformers", "model": "sentence-transformers/all-MiniLM-L6-v2",
             "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"}
MODEL = "gpt-6-astra"
BUDGET = 6000
TASKS = {
    "export": "Modernize write_batch: use JSONL v2 by default for new sites, while honoring existing deployment exceptions. Preserve explicit format overrides and iterable inputs. Run relevant tests.",
    "recovery": "Modernize write_recovery to use JSONL v2 by default for new sites while honoring existing deployment exceptions. Preserve journal reduction semantics and explicit format overrides. Run relevant tests.",
    "inventory": "Fix inventory.summarize so repeated SKUs have their quantities summed. Support a one-pass iterable and empty input. Keep export and recovery behavior unchanged. Run relevant tests.",
}
OPERATIONS = [
    {"role": "user", "content": "Operations handoff F-17: north's fulfillment appliance is independently deployed and accepts only CSV v1 (id,sku,quantity). It cannot ingest JSONL v2. South and newly onboarded sites accept JSONL v2. Preserve north's CSV routing until Operations confirms that its receiver has migrated; shipping this service does not upgrade it."},
    {"role": "user", "content": "Incident F-18: the north appliance polls both normal delivery and disaster-recovery replacement batches. They terminate at the same ingestion gateway despite their different service entry points. A normal-export change and a recovery-export change share the receiver compatibility obligation. Recovery must still apply latest-upsert/delete semantics. Review both paths whenever the receiver contract changes."},
    {"role": "user", "content": "These are reported deployment facts, not established by this repository's tests. Keep the deployment rule distinct from path-specific decisions if useful, and connect supported dependencies. Do not turn easily inspected function details into knowledge."},
]
MIGRATION = [{"role": "user", "content": "Operations handoff F-29 supersedes F-17/F-18's format exception: north's receiver has migrated and now accepts only JSONL v2. All retained recovery input has been converted; no CSV-only receiver remains supported. South and new sites remain JSONL v2. Both normal and recovery batches go through the new gateway. This is an operations report, not independent deployment verification. Retire or revise the old CSV advice and inspect dependent decisions while preserving the historical reason."}]


def hashes(path):
    return {str(p.relative_to(path)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}


def freeze(root):
    files = [Path(__file__), Path(__file__).with_name("fulfillment_grader.py"), *sorted(PROJECT.glob("*"))]
    dump(root / "protocol.json", {"model": MODEL, "embedding": EMBEDDING, "budget_utf8_bytes": BUDGET,
        "tasks": TASKS, "operations": OPERATIONS, "migration": MIGRATION,
        "files": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},
        "criteria": "Separate consumer checks; all attempts retained; no task tuning after actor outcomes.",
        "limitations": ["Synthetic operational reports, not real customer evidence.",
            "Controlled injected retrieval, not autonomous retrieval invocation.",
            "One run per condition: feasibility pilot, no statistical effect estimate.",
            "No-knowledge failures can reflect missing information; they do not establish model incompetence.",
            "Small captured corpus may make flat and graph evidence identical."]})


def base_trial(path):
    (path / "input").mkdir(parents=True)
    (path / "output").mkdir()
    shutil.copytree(PROJECT, path / "workspace" / "project", ignore=shutil.ignore_patterns("__pycache__"))


def prepare_skill(output, source=None):
    root = fresh(output)
    freeze(root)
    trial = root / ("maintenance" if source else "capture")
    base_trial(trial)
    code_base = init_repo(trial / "workspace/project", {})
    content = snapshot(source, "main")[1] if source else {}
    knowledge_base = init_repo(trial / "workspace/knowledge", content)
    skill = "knowledge-maintain" if source else "knowledge-extract"
    shutil.copytree(ROOT / "skills" / skill, trial / "input/skills" / skill)
    shutil.copytree(ROOT / "knowledge_agent", trial / "input/tool-source/knowledge_agent", ignore=shutil.ignore_patterns("__pycache__"))
    (trial / "input/applicable-skills").mkdir()
    dump(trial / "input/repositories.json", {"fulfillment": "/workspace/project"})
    dump(trial / "workspace/config.json", {"repo": "/workspace/knowledge", "branch": "main",
         "state": "/workspace/state", "embedding": EMBEDDING, "provider": None, "automatic_merge": False})
    if source:
        task = "Execute knowledge-maintain on the reported receiver migration. Inspect all relevant accepted nodes and dependencies. Prepare corrections for separate review; do not accept. No source-code change is supplied: the trigger is an external deployment condition change, not an anchor diff."
    else:
        task = "First change write_batch to stream iterable records directly rather than materialize them; preserve output and run tests. Then execute knowledge-extract on this task and the supplied operations conversation. Start from the empty store. Prepare proposals for separate review; do not accept. Do not force a number of nodes."
    dump(trial / "input/request.json", {"task": task, "conversation": MIGRATION if source else OPERATIONS,
        "project": "/workspace/project", "model": MODEL, "max_output_tokens": 8000,
        "skill": f"/input/skills/{skill}/SKILL.md", "applicable_skills": "/input/applicable-skills",
        "repositories": "/input/repositories.json", "code_base": code_base,
        "cli": "python -m knowledge_agent --config /workspace/config.json"})
    dump(trial / "private.json", {"kind": skill, "base_revision": knowledge_base,
         "source": str(source) if source else None, "starting_files": hashes(trial / "workspace/project")})
    return str(trial)


def contexts(index, embedder, query):
    view = index.view()
    ranked = index.search(view, query, embedder, limit=max(1, len(view.nodes)), candidates=max(1, len(view.nodes)))["results"]
    ids = [r["metadata"]["id"] for r in ranked]
    records = [{**view.nodes[key].as_dict(), "relationship_path": []} for key in ids]
    empty = _pack([], BUDGET)
    flat = _pack(records, BUDGET)
    graph = view.context(ids[0], depth=2, max_nodes=20, max_tokens=BUDGET) if ids else empty
    return {"none": empty, "flat": flat, "graph": graph}, ids


def prepare_reuse(output, source, era="before"):
    root = fresh(output)
    freeze(root)
    revision, corpus, _ = snapshot(source, "main")
    require(bool(corpus), "Capture produced no accepted knowledge; record capture failure before reuse")
    repo = root / "evaluator-knowledge"
    init_repo(repo, corpus)
    embedder = Embedder(EMBEDDING)
    index = Index(root / "evaluator-index")
    index.rebuild(repo, "main", embedder)
    trials = []
    exposure = {}
    selected = TASKS if era == "before" else {k: TASKS[k] for k in ("export", "recovery")}
    for task, text in selected.items():
        supplied, ranked = contexts(index, embedder, text)
        exposure[task] = {"ranked_ids": ranked, "contexts": supplied}
        for condition in (("none", "flat", "graph") if era == "before" else ("graph",)):
            tid = task + "-" + condition
            trial = root / tid
            base_trial(trial)
            dump(trial / "input/knowledge.json", supplied[condition])
            dump(trial / "input/request.json", {"task": text, "project": "/workspace/project",
                "knowledge": "/input/knowledge.json", "model": MODEL, "max_output_tokens": 8000,
                "instruction": "Use supplied knowledge when relevant, inspect code and run tests. Write implementation, not just recommendations. No operator is available in this isolated trial; record unresolved deployment uncertainty in your final response."})
            (trial / "grading").mkdir()
            shutil.copyfile(Path(__file__).with_name("fulfillment_grader.py"), trial / "grading/check.py")
            dump(trial / "grading/contract.json", {"task": task, "era": era})
            dump(trial / "private.json", {"task": task, "condition": condition, "era": era,
                "model": MODEL, "knowledge_source": str(source), "source_revision": revision,
                "context_used": supplied[condition]["estimated_tokens"],
                "starting_files": hashes(trial / "workspace/project")})
            trials.append(tid)
    random.Random(42).shuffle(trials)
    dump(root / "exposure.json", exposure)
    dump(root / "experiment.json", {"run_order": trials, "era": era, "model": MODEL,
        "source_revision": revision, "knowledge_provenance": "actual_reviewed_capture_unedited"})
    return trials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "maintain", "reuse"))
    parser.add_argument("output")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--era", choices=("before", "after"), default="before")
    args = parser.parse_args()
    if args.action != "capture":
        require(args.source is not None, "--source accepted knowledge repository required")
    print(json.dumps(prepare_reuse(args.output, args.source, args.era) if args.action == "reuse"
                     else prepare_skill(args.output, args.source if args.action == "maintain" else None)))


if __name__ == "__main__":
    main()
