"""Collect actual pilot evidence without turning narrative claims into scores."""
import argparse
import hashlib
import json
from pathlib import Path

from knowledge_agent.gitstore import git, snapshot
from .harness import dump, read


def report(root):
    trial = root / "investigation"
    trace = trial / "output/agent-trace.txt"
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    completed = [e["item"] for e in events if e.get("type") == "item.completed"]
    commands = [item for item in completed if item.get("type") == "command_execution"]
    submissions = []
    for command in commands:
        if " task-end " not in command.get("command", ""):
            continue
        output = command.get("aggregated_output", "")
        try:
            result, _ = json.JSONDecoder().raw_decode(output.lstrip())
        except ValueError:
            result = None
        submissions.append({"command": command["command"], "shell_exit_code": command.get("exit_code"),
                            "result": result})
    private = read(trial / "private.json")
    repo = trial / "workspace/knowledge"
    revision, nodes, _ = snapshot(repo, "main")
    branches = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/knowledge/").stdout.splitlines()
    turns = [e for e in events if e.get("type") == "turn.completed"]
    return {
        "kind": "basic_memory_standing_policy_pilot", "experiment": read(root / "experiment.json"),
        "execution": read(trial / "run.json"), "held_out_grade": read(trial / "grading-run.json"),
        "calibration": {name: read(root / name / "grading-run.json")
                        for name in ("calibration-before", "calibration-reference")},
        "submission_evidence": submissions,
        "knowledge": {"accepted_main_unchanged": revision == private["base_revision"],
                      "accepted_nodes": len(nodes), "proposal_branches": branches,
                      "working_tree_status": git(repo, "status", "--porcelain").stdout},
        "independent_test_output": (trial / "verification.txt").read_text(encoding="utf-8"),
        "native_usage": turns[-1].get("usage") if turns else None,
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "request_sha256": hashlib.sha256((trial / "input/request.json").read_bytes()).hexdigest(),
        "review": read(trial / "reviewer.json") if (trial / "reviewer.json").exists() else None,
        "status": "observed_requires_review" if not (trial / "reviewer.json").exists() else "reviewed_pilot",
        "reuse": "not_run_empty_corpus" if not nodes and not branches else "not_run",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dump(args.output, report(args.directory))
