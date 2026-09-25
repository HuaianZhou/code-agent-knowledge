"""Collect trigger evidence; semantic correctness still requires explicit review."""
import argparse
import hashlib
import json
from pathlib import Path

from knowledge_agent.gitstore import git, snapshot
from .harness import dump, read


def report(root):
    experiment = read(root / "experiment.json")
    rows = []
    for tid in experiment["run_order"]:
        trial = root / tid
        trace = trial / "output/agent-trace.txt"
        events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
        commands = [e["item"] for e in events if e.get("type") == "item.completed"
                    and e.get("item", {}).get("type") == "command_execution"]
        captures = [c for c in commands if c.get("exit_code") == 0 and
                    any(word in c.get("command", "") for word in (" task-end ", " propose "))]
        messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                    and e.get("item", {}).get("type") == "agent_message"]
        turns = [e for e in events if e.get("type") == "turn.completed"]
        private = read(trial / "private.json")
        repo = trial / "workspace/knowledge"
        branches = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/knowledge/").stdout.splitlines()
        revision, accepted, _ = snapshot(repo, "main")
        proposed = [{"branch": branch, "revision": snapshot(repo, branch)[0],
                     "nodes": [node.as_dict() for node in snapshot(repo, branch)[1].values()]} for branch in branches]
        row = {"case": private["case"], "request": read(trial / "input/request.json"),
            "execution": read(trial / "run.json"), "coding_grade": read(trial / "grading-run.json"),
            "policy": (trial / "workspace/project/AGENTS.md").read_text(encoding="utf-8"),
            "policy_sha256": private["policy_sha256"], "source_hashes": experiment["source_hashes"],
            "capture_command_candidates": captures, "accepted_main_unchanged": revision == private["base_revision"],
            "accepted_nodes": len(accepted), "accepted_checkout_status": git(repo, "status", "--porcelain").stdout,
            "proposals": proposed, "native_usage": turns[-1].get("usage") if turns else None,
            "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
            "final_response": messages[-1] if messages else None,
            "review": read(trial / "reviewer.json") if (trial / "reviewer.json").exists() else None}
        rows.append(row)
    return {"kind": "standing_policy_capture", "model": experiment["model"], "trials": rows,
        "limitation": "Two synthetic trials. Tests standing AGENTS.md compliance, not a deterministic host hook, skill-description-only discovery, or reliability under interruptions. Command matching is evidence for review, not a semantic score."}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = report(args.directory)
    dump(args.output, result)
    print(json.dumps([{ "case": r["case"], "capture_commands": len(r["capture_command_candidates"]),
        "proposals": len(r["proposals"]), "coding_exit_code": r["coding_grade"]["exit_code"]} for r in result["trials"]]))
