"""Collect native retrieval evidence and separately graded code outcomes."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

from knowledge_agent.gitstore import git, snapshot
from .fulfillment import PROJECT
from .harness import dump, read


def report(root):
    experiment = read(root / "experiment.json")
    rows = []
    for tid in experiment["run_order"]:
        trial = root / tid
        private = read(trial / "private.json")
        trace = trial / "output/agent-trace.txt"
        events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()] if trace.exists() else []
        items = [(i, e["item"]) for i, e in enumerate(events) if e.get("type") == "item.completed"]
        calls = [{"event_index": i, **item} for i, item in items if item.get("type") == "command_execution"
                 and "knowledge_agent" in item.get("command", "")]
        messages = [item["text"] for _, item in items if item.get("type") == "agent_message"]
        turns = [e for e in events if e.get("type") == "turn.completed"]
        repo = trial / "workspace/knowledge"
        diffs = {p.name: "".join(difflib.unified_diff(p.read_text(encoding="utf-8").splitlines(True),
                 (trial / "workspace/project" / p.name).read_text(encoding="utf-8").splitlines(True),
                 fromfile="before/" + p.name, tofile="after/" + p.name)) for p in PROJECT.glob("*.py")}
        execution = read(trial / "run.json") if (trial / "run.json").exists() else None
        grade = read(trial / "grading-run.json") if (trial / "grading-run.json").exists() else None
        result = read(trial / "output/result.json") if (trial / "output/result.json").exists() else {}
        status = "pending" if not execution else "invalid_execution" if execution["exit_code"] or result.get("model") != experiment["model"] else "passed" if grade and grade["exit_code"] == 0 else "failed" if grade else "needs_grading"
        rows.append({"task": tid, "directory": str(trial), "status": status, "request": read(trial / "input/request.json"), "private": private,
            "execution": execution, "coding_grade": grade,
            "grader_output": (trial / "grading.stderr.txt").read_text(encoding="utf-8") if grade else None,
            "infrastructure_error": "usage_limit" if any(e.get("type") in ("error", "turn.failed") and "usage limit" in json.dumps(e).lower() for e in events) else None,
            "knowledge_cli_commands": calls, "implementation_diffs": diffs,
            "knowledge_unchanged": snapshot(repo, "main")[0] == private["knowledge_base"]
                and not git(repo, "status", "--porcelain").stdout,
            "proposal_branches": git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/knowledge/").stdout.splitlines(),
            "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest() if trace.exists() else None,
            "native_usage": turns[-1].get("usage") if turns else None,
            "final_response": messages[-1] if messages else None,
            "review": read(trial / "reviewer.json") if (trial / "reviewer.json").exists() else None})
    return {"kind": "on_demand_retrieval", "experiment": experiment, "trials": rows,
            "note": "Interpret native commands and actual code changes together. Consumer success alone does not prove knowledge use; no-retrieval may be correct on the inventory control."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [report(root) for root in args.directories]
    result = {"kind": "on_demand_retrieval", "experiments": [r["experiment"] for r in reports],
              "trials": [t for r in reports for t in r["trials"]], "note": reports[0]["note"]}
    completed = {r["task"] for r in result["trials"] if r["status"] in ("passed", "failed")}
    for row in result["trials"]:
        if row["status"] == "pending" and row["task"] in completed:
            row["status"] = "unused_preparation"
    dump(args.output, result)
    print(json.dumps([{ "task": r["task"], "knowledge_commands": len(r["knowledge_cli_commands"]),
        "status": r["status"], "knowledge_unchanged": r["knowledge_unchanged"]} for r in result["trials"]]))
