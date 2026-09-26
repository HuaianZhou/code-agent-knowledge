"""Fresh coding sessions choose retrieval; no nodes or queries in task prompts."""
import argparse
import hashlib
from pathlib import Path
import random
import shutil

from knowledge_agent.gitstore import git, snapshot
from .fulfillment import MODEL, EMBEDDING, TASKS, base_trial, hashes
from .harness import ROOT, dump, fresh, init_repo


def prepare(output, source):
    root = fresh(output)
    source_revision, corpus, _ = snapshot(source, "main")
    template = ROOT / "integrations/codex/retrieval.fragment.md"
    policy = template.read_text(encoding="utf-8").replace("{{CLI_COMMAND}}", "python -m knowledge_agent --config /workspace/config.json").replace(
        "{{SKILL_PATH}}", "/input/skills/knowledge-retrieve/SKILL.md").replace("{{REPOSITORIES_PATH}}", "/input/repositories.json")
    trials = []
    for task, prompt in TASKS.items():
        trial = root / task
        base_trial(trial)
        project = trial / "workspace/project"
        (project / "AGENTS.md").write_text(policy, encoding="utf-8")
        init_repo(project, {})
        knowledge_base = init_repo(trial / "workspace/knowledge", corpus)
        shutil.copytree(ROOT / "skills/knowledge-retrieve", trial / "input/skills/knowledge-retrieve")
        shutil.copytree(ROOT / "knowledge_agent", trial / "input/tool-source/knowledge_agent", ignore=shutil.ignore_patterns("__pycache__"))
        (trial / "input/applicable-skills").mkdir()
        dump(trial / "input/repositories.json", {"fulfillment": "/workspace/project"})
        dump(trial / "workspace/config.json", {"repo": "/workspace/knowledge", "branch": "main",
            "state": "/workspace/state", "embedding": EMBEDDING, "provider": None, "automatic_merge": False})
        dump(trial / "input/request.json", {"task": prompt, "project": "/workspace/project", "model": MODEL, "max_output_tokens": 8000})
        (trial / "grading").mkdir()
        shutil.copyfile(ROOT / "evaluation/fulfillment_grader.py", trial / "grading/check.py")
        dump(trial / "grading/contract.json", {"task": task, "era": "before"})
        dump(trial / "private.json", {"task": task, "knowledge_base": knowledge_base, "source_revision": source_revision,
             "starting_files": hashes(project), "policy_sha256": hashlib.sha256(policy.encode()).hexdigest()})
        trials.append(task)
    random.Random(42).shuffle(trials)
    dump(root / "experiment.json", {"run_order": trials, "model": MODEL, "source_revision": source_revision,
        "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), template, ROOT / "skills/knowledge-retrieve/SKILL.md", ROOT / "evaluation/fulfillment_grader.py")},
        "criteria": "Review native trace for agent-chosen queries, relevant evidence before implementation, and appropriate restraint on inventory. Separate consumer grades assess code. No fixed node IDs or queries supplied to actor.",
        "limitation": "Three synthetic sessions with standing retrieval policy; not unaided discovery, no end-to-end retrieval token cap, not an equal-cost comparison to injected contexts."})
    return str(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.output, args.source))
