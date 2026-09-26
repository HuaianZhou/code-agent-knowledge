"""Prepare retrieval-policy cases; agent judgments require separate trace review."""
import argparse
import hashlib
from pathlib import Path
import shutil

from knowledge_agent.model import Node
from .fulfillment import EMBEDDING, MODEL
from .harness import ROOT, dump, fresh, init_repo


CASES = {
    "metadata_hit": {
        "task": "In the orders project, what must we preserve when extending stored state values? The project uses the tag storage for this guidance.",
        "targets": ["kn-archive"],
        "criterion": "Try the justified storage tag; read and explain stable numeric meanings and the independently deployed archive reader. Broader search is allowed if needed.",
    },
    "empty_metadata": {
        "task": "In orders, investigate safe retries after a charge request times out. A teammate suggests trying the tag retries, but is unsure it exists.",
        "targets": ["kn-partner"],
        "criterion": "If retries is attempted it returns empty; remove that filter and search content. Query outcome before resending a possibly completed charge. Direct content search is acceptable; record whether fallback was actually exercised.",
    },
    "weak_metadata": {
        "task": "In orders, decide whether to resend a charge after losing its response. There is a retry tag in the store; it might help.",
        "targets": ["kn-partner"],
        "criterion": "The retry-tag timer node is nonempty but cannot resolve duplicate charging. Broaden content search and find the partner rule; do not mistake topical results for sufficient evidence.",
    },
    "detailed_question": {
        "task": "In orders, the bank connection closed after we sent a charge and before we received its answer. Can resending bill the customer twice? Explain the safe next action from project knowledge.",
        "targets": ["kn-partner"],
        "criterion": "No tag is supplied. Use content search without inventing a required tag. Discover the body-only non-idempotency detail beneath the generic Partner agreement title; explain status reconciliation.",
    },
    "anchor_entry": {
        "task": "Review orders/writer.py before changing persisted state numbers. What project obligations should guide the change?",
        "targets": ["kn-writer", "kn-archive", "kn-restoration"],
        "criterion": "Use the known file as an anchor entry, then inspect connected evidence. Include the archive-reader constraint and the separate restoration verification obligation.",
    },
    "weak_title_neighbor": {
        "task": "In orders, extend the order lifecycle with a new stored state. What implementation and verification obligations should we follow?",
        "targets": ["kn-archive", "kn-restoration"],
        "criterion": "Discover the connected Continuity rehearsal node and its restore check despite its unobvious title. Record whether it came from search or graph expansion; do not claim graph benefit if search already delivered it.",
    },
    "wrong_type": {
        "task": "In orders, investigate tenant isolation in shared memoization. I expect a decision node, but that classification may be wrong.",
        "targets": ["kn-cache"],
        "criterion": "A decision-only filter misses the relevant constraint. Drop uncertain type restrictions and find tenant identity in cache keys. Direct unrestricted retrieval is acceptable; record the actual route.",
    },
    "no_evidence": {
        "task": "What quantum-resistant signature algorithm has the orders team approved for exports? Look for recorded project evidence; do not make a new recommendation.",
        "targets": [],
        "criterion": "Search may return unrelated nearest neighbors. Report no supporting recorded decision within searched scope, not invented approval or certainty that none exists anywhere.",
    },
}


def corpus(code_revision):
    specs = [
        ("kn-writer", "Order lifecycle implementation", "decision", ["lifecycle"],
         ["kn-archive"], "writer.py",
         "For stored order state changes, consult the archive-reader contract and preserve old meanings while adding a new value."),
        ("kn-archive", "Archive interpretation agreement", "constraint", ["storage"], [], None,
         "Retained unversioned records use NEW=0, PAID=1 and CANCELLED=2. An independently deployed appliance reads seven years of archives. Preserve those meanings until records and all supported readers migrate together; a writer release does not upgrade the reader."),
        ("kn-restoration", "Continuity rehearsal", "verification_rule", ["operations"],
         ["kn-archive"], None,
         "When introducing a stored lifecycle value, validate a restore using both a retained archive and a new record against the supported appliance. The deployment gate requires this rehearsal; an in-process encoder round trip does not cover it."),
        ("kn-partner", "Partner agreement", "constraint", ["integrations"], [], None,
         "The bank's legacy charging endpoint has no idempotency protection. A dropped response can follow a successful debit. Before sending again, reconcile the transaction status through the partner inquiry interface; an unresolved outcome needs operator reconciliation, not a blind replay. Reassess when the partner contract changes."),
        ("kn-timer", "Retry timing", "mechanism", ["retry"], [], None,
         "Measure retry deadlines with a monotonic clock, because wall-clock adjustments can extend the elapsed timeout. This timing rule does not establish whether repeating an operation is safe."),
        ("kn-cache", "Shared memoization boundary", "constraint", ["isolation"], [], None,
         "Shared workers serve multiple tenants with overlapping object IDs. Include tenant identity in cache keys or one tenant may receive another's cached result. Reassess if workers become tenant-exclusive."),
        ("kn-noise", "Console formatting", "decision", ["diagnostics"], [], None,
         "Operations uses plain text diagnostic output in its legacy terminal collector; retain plain text until that collector is replaced."),
    ]
    nodes = {}
    for key, title, kind, tags, targets, path, body in specs:
        nodes[key] = Node({"schema_version": 1, "id": key, "title": title, "type": kind,
            "tags": tags, "weight": .6, "status": "active",
            "scope": {"repositories": ["orders"], "conditions": ["Synthetic reported deployment"]},
            "evidence_state": "reported", "sources": [{"kind": "human", "reference": "Synthetic operations fixture"}],
            "verification": {}, "relations": [{"type": "related_nodes", "target": t} for t in targets],
            "anchors": [{"repo": "orders", "path": path, "role": "affected_code", "verified_commit": code_revision}] if path else []},
            body, f"nodes/{key}.md")
    return nodes


def prepare(output):
    root = fresh(output)
    template = ROOT / "integrations/codex/retrieval.fragment.md"
    skill = ROOT / "skills/knowledge-retrieve/SKILL.md"
    policy = template.read_text(encoding="utf-8").replace("{{SKILL_PATH}}", "/input/skills/knowledge-retrieve/SKILL.md").replace(
        "{{CLI_COMMAND}}", "python -m knowledge_agent --config /workspace/config.json").replace("{{REPOSITORIES_PATH}}", "/input/repositories.json")
    for name, case in CASES.items():
        trial = root / name
        (trial / "input").mkdir(parents=True)
        (trial / "output").mkdir()
        project = trial / "workspace/project"
        project.mkdir(parents=True)
        (project / "AGENTS.md").write_text(policy, encoding="utf-8")
        (project / "writer.py").write_text('STATES = {"NEW": 0, "PAID": 1, "CANCELLED": 2}\n', encoding="utf-8")
        code_base = init_repo(project, {})
        knowledge_base = init_repo(trial / "workspace/knowledge", corpus(code_base))
        shutil.copytree(skill.parent, trial / "input/skills/knowledge-retrieve")
        shutil.copytree(ROOT / "knowledge_agent", trial / "input/tool-source/knowledge_agent", ignore=shutil.ignore_patterns("__pycache__"))
        (trial / "input/applicable-skills").mkdir()
        dump(trial / "input/repositories.json", {"orders": "/workspace/project"})
        dump(trial / "workspace/config.json", {"repo": "/workspace/knowledge", "branch": "main",
            "state": "/workspace/state", "embedding": EMBEDDING, "provider": None, "automatic_merge": False})
        dump(trial / "input/request.json", {"task": case["task"] + " Return findings only; do not change code or knowledge.",
            "project": "/workspace/project", "model": MODEL, "max_output_tokens": 6000})
        dump(trial / "private.json", {**case, "knowledge_base": knowledge_base, "code_base": code_base,
            "status": "prepared_not_run", "review": {"retrieval_route": None, "evidence_used": None,
                "answer_supported": None, "no_writes": None, "budget_and_gaps": None}})
    dump(root / "experiment.json", {"model": MODEL, "run_order": list(CASES), "status": "prepared_not_run",
        "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), template, skill)},
        "criteria": "Private semantic review of native trace, answers and unchanged Git stores; command presence alone is not success."})
    return str(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    print(prepare(parser.parse_args().output))
