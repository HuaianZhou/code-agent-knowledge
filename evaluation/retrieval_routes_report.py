"""Collect retrieval-route evidence; answer quality requires recorded evaluator review."""
import argparse
import hashlib
import json
from pathlib import Path

from knowledge_agent.gitstore import git
from .harness import ROOT, dump, read


def report(root):
    experiment = read(root / "experiment.json")
    rows = []
    for name in experiment["run_order"]:
        trial = root / name
        private = read(trial / "private.json")
        trace = trial / "output/agent-trace.txt"
        events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()] if trace.exists() else []
        items = [(i, e["item"]) for i, e in enumerate(events) if e.get("type") == "item.completed"]
        commands = [(i, x) for i, x in items if x.get("type") == "command_execution"]
        messages = [x["text"] for _, x in items if x.get("type") == "agent_message"]
        usage = [e.get("usage") for e in events if e.get("type") == "turn.completed"]
        execution = read(trial / "run.json") if (trial / "run.json").exists() else None
        result = read(trial / "output/result.json") if (trial / "output/result.json").exists() else {}
        review = read(trial / "reviewer.json") if (trial / "reviewer.json").exists() else None
        stores = {}
        for folder, base in (("knowledge", private["knowledge_base"]), ("project", private["code_base"])):
            repo = trial / "workspace" / folder
            stores[folder] = {"base": base, "head": git(repo, "rev-parse", "HEAD").stdout.strip(),
                "status": git(repo, "status", "--porcelain").stdout,
                "proposal_branches": git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/knowledge/").stdout.splitlines()}
        unchanged = all(s["head"] == s["base"] and not s["status"] and not s["proposal_branches"] for s in stores.values())
        status = "pending"
        if execution:
            if execution["exit_code"] or result.get("model") != experiment["model"]:
                status = "invalid_execution"
            elif not unchanged:
                status = "failed"
            elif review:
                if review.get("answer_supported") is False or review.get("no_writes") is False:
                    status = "failed"
                else:
                    status = "passed" if review.get("answer_supported") is True and review.get("no_writes") is True else "needs_review"
            else:
                status = "needs_review"
        rows.append({"case": name, "status": status, "request": read(trial / "input/request.json"),
            "criterion": private["criterion"], "expected_targets": private["targets"], "execution": execution,
            "stores": stores, "unchanged": unchanged,
            "knowledge_commands": [{"event_index": i, **x} for i, x in commands if "knowledge_agent" in x["command"]],
            "all_commands": [{"event_index": i, "command": x["command"], "exit_code": x.get("exit_code")} for i, x in commands],
            "file_changes": [{"event_index": i, **x} for i, x in items if x.get("type") == "file_change"],
            "final_response": messages[-1] if messages else None, "review": review,
            "native_usage": usage[-1] if usage else None,
            "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest() if trace.exists() else None})
    return {"experiment": experiment, "source_hashes_match": all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                for p, h in experiment["source_hashes"].items()),
            "calibration": read(root / "calibration.json") if (root / "calibration.json").exists() else None,
            "trials": rows,
            "limitations": "Synthetic seven-node corpus; parent evaluator review, not blind human review. Correct answers do not imply every optional route was exercised. No policy comparison or reliability estimate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.directory)
    dump(args.output, result)
    print(json.dumps([{ "case": r["case"], "status": r["status"], "unchanged": r["unchanged"]} for r in result["trials"]]))
