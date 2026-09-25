"""Assemble actual executions without treating agent claims as a pass."""
import argparse
import difflib
import hashlib
from pathlib import Path
import json

from .harness import read, dump
from .fulfillment import hashes, PROJECT


def report(roots):
    rows = []
    protocols = []
    for root in roots:
        protocol = read(root / "protocol.json")
        protocols.append({"directory": str(root), **protocol})
        experiment = read(root / "experiment.json") if (root / "experiment.json").exists() else None
        trials = [root / tid for tid in experiment["run_order"]] if experiment else [p for p in root.iterdir() if (p / "private.json").exists()]
        for trial in trials:
            private = read(trial / "private.json")
            execution = read(trial / "run.json") if (trial / "run.json").exists() else None
            grade = read(trial / "grading-run.json") if (trial / "grading-run.json").exists() else None
            trace = trial / "output/agent-trace.txt"
            events = []
            if trace.exists():
                for line in trace.read_text(encoding="utf-8").splitlines():
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        pass
            turns = [e for e in events if e.get("type") == "turn.completed"]
            commands = [e["item"] for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution"]
            artifact = read(trial / "output/result.json") if (trial / "output/result.json").exists() else {}
            status = "pending" if not execution else "invalid_execution" if execution["exit_code"] or artifact.get("model") != protocol["model"] else "passed" if grade and grade["exit_code"] == 0 else "failed" if grade else "needs_review"
            row = {"directory": str(trial), "status": status, "private": private, "execution": execution,
                "grading": grade, "native_usage": turns[-1].get("usage") if turns else None,
                "completed_commands": len(commands), "final_files": hashes(trial / "workspace/project"),
                "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest() if trace.exists() else None}
            row["infrastructure_error"] = "usage_limit" if any(
                e.get("type") in ("error", "turn.failed") and "usage limit" in json.dumps(e).lower()
                for e in events) else None
            messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                        and e.get("item", {}).get("type") == "agent_message"]
            row["agent_final_response"] = messages[-1] if messages else None
            row["implementation_diffs"] = {}
            for name in ("exporter.py", "recovery.py", "inventory.py", "wire_formats.py"):
                actual = trial / "workspace/project" / name
                if actual.exists():
                    row["implementation_diffs"][name] = "".join(difflib.unified_diff(
                        (PROJECT / name).read_text(encoding="utf-8").splitlines(True),
                        actual.read_text(encoding="utf-8").splitlines(True), fromfile="before/" + name, tofile="after/" + name))
            row["added_python_files"] = {p.name: p.read_text(encoding="utf-8")
                for p in (trial / "workspace/project").glob("*.py") if not (PROJECT / p.name).exists()}
            if grade:
                row["grader_output"] = (trial / "grading.stderr.txt").read_text(encoding="utf-8")
                row["grader_sha256"] = hashlib.sha256((trial / "grading/check.py").read_bytes()).hexdigest()
                row["consumer_contract"] = read(trial / "grading/contract.json")
            if (trial / "reviewer.json").exists():
                row["review"] = read(trial / "reviewer.json")
                if (row["status"] == "needs_review" and row["review"].get("decision") == "acceptable"
                        and row["review"].get("acceptance", {}).get("outcome") == "accepted"):
                    row["status"] = "accepted_after_review"
            if (trial / "input/knowledge.json").exists():
                context = read(trial / "input/knowledge.json")
                row["context"] = context
            rows.append(row)
    def cell(row):
        p = row["private"]
        return tuple(p.get(k) for k in ("era", "source_revision", "task", "condition"))

    completed_cells = {cell(row) for row in rows if row["status"] in ("passed", "failed")}
    for row in rows:
        if row["status"] == "pending" and cell(row) in completed_cells:
            row["status"] = "unused_preparation"
    groups = {}
    for row in rows:
        if row["status"] not in ("passed", "failed"):
            continue
        private = row["private"]
        key = (private["era"], private["source_revision"], private["condition"])
        group = groups.setdefault(key, {"era": key[0], "source_revision": key[1],
            "condition": key[2], "passed": 0, "total": 0, "tasks": []})
        group["total"] += 1
        group["passed"] += row["status"] == "passed"
        group["tasks"].append({"task": private["task"], "status": row["status"], "directory": row["directory"]})
    return {"fixture": "fulfillment", "protocols": protocols, "trials": rows,
            "behavioral_summary": list(groups.values()),
            "adoption_conclusion": None, "note": "Behavioral grades are separate consumer checks; capture and maintenance require recorded semantic review. All attempts must be retained."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = report(args.roots)
    dump(args.output, result)
    print(json.dumps([{ "trial": r["directory"], "status": r["status"]} for r in result["trials"]], indent=2))


if __name__ == "__main__":
    main()
