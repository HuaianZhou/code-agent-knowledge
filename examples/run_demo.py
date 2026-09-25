"""Run a complete local loop against two repos and a local bare remote.

Run from the project root: python -m examples.run_demo --directory .demo
All assertions concern deterministic mechanics, not autonomous agent quality.
"""
from pathlib import Path
import argparse
import json

from knowledge_agent.gitstore import git, initialize, synchronize
from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import Node, require
from knowledge_agent.workflow import propose, review, review_impact


def init_repo(path):
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Knowledge Demo")
    git(path, "config", "user.email", "demo@example.invalid")


def commit(path, message):
    git(path, "add", ".")
    git(path, "commit", "-m", message)
    return git(path, "rev-parse", "HEAD").stdout.strip()


def run(directory):
    root = Path(directory).resolve()
    require(not root.exists(), "demo destination must not exist; choose a fresh directory")
    code, knowledge = root / "orders", root / "knowledge"
    init_repo(code)
    (code / "writer.py").write_text('''from enum import IntEnum
import json

class State(IntEnum):
    NEW = 0
    PAID = 1
    CANCELLED = 2

def append_order(stream, order_id, state):
    stream.write(json.dumps({"id": order_id, "state": int(state)}) + "\\n")
''', encoding="utf-8")
    (code / "recovery.py").write_text('''import json

def replay(stream):
    # Deployed as a separate recovery utility.
    return [(row["id"], {0: "new", 1: "paid", 2: "cancelled"}[row["state"]])
            for row in map(json.loads, stream)]
''', encoding="utf-8")
    (code / "OPERATIONS.md").write_text(
        "Synthetic human correction: retained journals can be replayed by recovery utilities "
        "deployed independently of the writer. Deployment alone does not migrate retained data.\n", encoding="utf-8")
    code_rev = commit(code, "Synthetic independently deployed writer and recovery utility")
    init_repo(knowledge)
    (knowledge / "README.md").write_text("Synthetic knowledge fixtures; not company facts.\n", encoding="utf-8")
    commit(knowledge, "Create empty knowledge repository")
    remote = root / "shared.git"
    git(root, "clone", "--bare", knowledge, remote)
    git(knowledge, "remote", "add", "origin", remote)
    config_path = root / "client" / "config.json"
    config = initialize(config_path, knowledge)
    index = Index(config["state"])
    embedder = Embedder(config["embedding"])
    index.rebuild(knowledge, "main", embedder)
    candidates = root / "candidates"
    candidates.mkdir()
    definitions = [
        ("kn-journal-compatibility", "Retained journal ordinals cross deployment boundaries", "constraint", [],
         "When modifying order state values, retain existing numeric encodings or migrate retained journals "
         "and coordinate recovery readers. Deployment does not migrate old records. Human guidance establishes "
         "independent recovery deployment; the writer enum and recovery decoder establish the encoding dependency. "
         "Reassess when versioned journal records and migration coverage are established."),
        ("kn-writer-change", "Append new order states without renumbering existing values", "decision",
         [{"type": "related_nodes", "target": "kn-journal-compatibility"}],
         "When adding a writer state, allocate a new numeric value and verify old-journal replay. "
         "Do not infer that upgrading the writer also upgrades recovery. Reassess for a versioned format."),
        ("kn-recovery-change", "Check retained journal versions before changing recovery", "verification_rule",
         [{"type": "related_nodes", "target": "kn-journal-compatibility"}],
         "When changing recovery, replay retained records from supported writer versions before rollout. "
         "The retained-data constraint applies independently of writer deployment. Reassess after migration.")]
    manifest = {"nodes": [], "admission": [], "operations": {}}
    for key, title, kind, relations, body in definitions:
        meta = {"schema_version": 1, "id": key, "title": title, "type": kind, "tags": ["orders", "journal"],
                "weight": .9 if kind == "constraint" else .7, "status": "active",
                "scope": {"repositories": ["orders"], "conditions": ["unversioned journals", "independent recovery deployments"]},
                "evidence_state": "reported", "anchors": [
                    {"repo": "orders", "path": "writer.py", "symbol": "State", "role": "affected_code", "verified_commit": code_rev},
                    {"repo": "orders", "path": "recovery.py", "symbol": "replay", "role": "evidence", "verified_commit": code_rev}],
                "relations": relations, "sources": [{"kind": "human", "reference": f"orders@{code_rev}:OPERATIONS.md (synthetic fixture)"}],
                "verification": {}}
        path = candidates / f"{key}.md"
        path.write_text(Node(meta, body).markdown(), encoding="utf-8")
        manifest["nodes"].append(str(path))
        manifest["operations"][key] = "create"
        manifest["admission"].append({"id": key,
            "not_cheaply_recoverable": {"passes": True, "reason": "Combines retained-data operations guidance with independent readers and writers."},
            "not_skill_duplicate": {"passes": True, "reason": "Fixture has no skill covering this deployment-specific condition."},
            "actionable": {"passes": True, "reason": "Changes encoding/migration and verification decisions."},
            "future_use": {"passes": True, "reason": "Applies to both new states and future recovery edits."},
            "existing_knowledge_search": "Fixture accepted repository is empty; A and C reuse B within this proposal."})
    (candidates / "proposal.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (candidates / "zero.json").write_text('{"nodes": [], "admission": []}\n', encoding="utf-8")
    zero = propose(config, {"nodes": [], "admission": []})
    proposal = propose(config, manifest)
    require(proposal["committed"], "demo proposal commit failed")
    report = review(config, proposal["branch"], index, embedder)
    require(not report["conflicting_ids"] and not report["integrity_errors"], "fixture review failed")
    # This controlled fixture explicitly accepts hand-authored data; product never auto-merges.
    git(knowledge, "merge", "--ff-only", proposal["branch"])
    git(knowledge, "push", "origin", "main")
    reader_config = initialize(root / "reader-client" / "config.json", root / "reader", str(remote))
    synced = synchronize(reader_config)
    reader_index = Index(reader_config["state"])
    reader_index.rebuild(reader_config["repo"], synced["revision"], embedder)
    context = reader_index.view().context("kn-writer-change", max_tokens=12000)
    require(len(context["results"]) == 3, "graph expansion failed")
    git(code, "mv", "recovery.py", "journal_recovery.py")
    commit(code, "Move recovery code without changing the constraint")
    impact = review_impact(reader_index.view(), "orders", code_repo=code, base=code_rev)
    result = {"config": str(config_path), "reader_config": str(root / "reader-client" / "config.json"),
              "zero_write": zero, "proposal": proposal, "review": report,
              "retrieval": context, "code_change_review": impact,
              "evaluation": "Hand-authored fixtures validate mechanics only, not autonomous extraction or behavioral improvement."}
    (root / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"results": str(root / "results.json"), "reader_config": result["reader_config"],
                      "retrieved_ids": [r["metadata"]["id"] for r in context["results"]],
                      "anchor_moves": impact["suggested_anchor_moves"], "zero_writes": zero["writes"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=".demo")
    run(parser.parse_args().directory)
