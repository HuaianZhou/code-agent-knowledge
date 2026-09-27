import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from evaluation.basic_memory import export_snapshot, prepare
from evaluation.harness import init_repo, read
from knowledge_agent.gitstore import git


class BasicMemoryPreparationTests(unittest.TestCase):
    def test_snapshot_excludes_future_history_and_request_has_no_capture_reminder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "AGENTS.md").write_text("Original project guidance.\n", encoding="utf-8")
            for name in ("pyproject.toml", "uv.lock"):
                (source / name).write_text("# historical metadata\n", encoding="utf-8")
            base = init_repo(source, {})
            (source / "later-solution.txt").write_text("future answer", encoding="utf-8")
            git(source, "add", ".")
            git(source, "commit", "-m", "Future solution must not leak")
            with patch("evaluation.basic_memory.export_snapshot", side_effect=lambda src, dst: export_snapshot(src, dst, base)), patch("evaluation.basic_memory.prepare_grading"):
                prepare(root / "trial", source)
            trial = root / "trial/investigation"
            project = trial / "workspace/project"
            self.assertFalse((project / "later-solution.txt").exists())
            self.assertNotIn("Future solution", git(project, "log", "--oneline").stdout)
            policy = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(policy.startswith("Original project guidance."))
            self.assertIn("knowledge-extract", policy)
            request = read(trial / "input/request.json")
            self.assertNotIn("capture", str(request).lower())
            self.assertNotIn("knowledge-extract", str(request))
            self.assertNotIn("cli", request)
            self.assertNotIn("1163", (trial / "input/incident.md").read_text())
            self.assertEqual(git(trial / "workspace/knowledge", "branch", "--list", "knowledge/*").stdout, "")


if __name__ == "__main__":
    unittest.main()
