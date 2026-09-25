"""Evaluate task-end capture via standing AGENTS.md, without per-task invocation."""
import argparse
import hashlib
from pathlib import Path

from .fulfillment import MODEL, OPERATIONS, TASKS, prepare_skill, hashes
from .harness import ROOT, dump, read
from knowledge_agent.gitstore import git

STREAM_GRADE = '''import io, unittest, sys
sys.path.insert(0, "/workspace/project")
from exporter import write_batch
from wire_formats import decode
class Streaming(unittest.TestCase):
    def test_streaming_and_preservation(self):
        rows = [{"id":"s-1","sku":"blue,large","quantity":2}, {"id":"s-2","sku":"x","quantity":3}]
        for fmt in ("csv-v1", "jsonl-v2"):
            out = io.StringIO()
            def records():
                yield rows[0]
                self.assertIn("s-1", out.getvalue())
                yield rows[1]
            write_batch("north", records(), out, fmt)
            self.assertEqual(decode(io.StringIO(out.getvalue()), fmt), rows)
if __name__ == "__main__":
    unittest.main()
'''


def prepare(output):
    root = Path(output).resolve()
    if root.exists():
        raise ValueError("Use a fresh output directory")
    root.mkdir(parents=True)
    template = ROOT / "integrations/codex/AGENTS.fragment.md"
    policy = template.read_text(encoding="utf-8").replace("{{SKILL_PATH}}", "/input/skills/knowledge-extract/SKILL.md").replace(
        "{{CLI_COMMAND}}", "python -m knowledge_agent --config /workspace/config.json").replace(
        "{{REPOSITORIES_PATH}}", "/input/repositories.json")
    trials = []
    for case in ("qualifying", "zero_value"):
        trial = Path(prepare_skill(root / case))
        project = trial / "workspace/project"
        (project / "AGENTS.md").write_text(policy, encoding="utf-8")
        git(project, "add", "AGENTS.md")
        git(project, "commit", "-m", "Configure standing task-end capture policy")
        request = {"task": "Change write_batch to stream iterable records directly rather than materialize them. Preserve output and run relevant tests." if case == "qualifying" else TASKS["inventory"],
            "project": "/workspace/project", "model": MODEL, "max_output_tokens": 8000}
        if case == "qualifying":
            # Keep operational evidence; omit the original capture/organization guidance.
            request["conversation"] = OPERATIONS[:2]
        dump(trial / "input/request.json", request)
        private = read(trial / "private.json")
        private.update(case=case, starting_files=hashes(project), trigger="standing_AGENTS_policy",
            expected="reported north constraint proposed" if case == "qualifying" else "zero-write task-end",
            policy_sha256=hashlib.sha256(policy.encode()).hexdigest())
        dump(trial / "private.json", private)
        (trial / "grading").mkdir()
        if case == "qualifying":
            (trial / "grading/check.py").write_text(STREAM_GRADE, encoding="utf-8")
        else:
            (trial / "grading/check.py").write_bytes((ROOT / "evaluation/fulfillment_grader.py").read_bytes())
            dump(trial / "grading/contract.json", {"task": "inventory", "era": "before"})
        trials.append(str(trial.relative_to(root)).replace("\\", "/"))
    dump(root / "experiment.json", {"model": MODEL, "run_order": trials,
        "protocol": "Standing project policy only; task request contains no capture instruction or skill pointer. Coding graded separately; native trace and Git proposals require evaluator review.",
        "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), template)}, "status": "prepared_not_run"})
    return str(root)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output")
    print(prepare(p.parse_args().output))
