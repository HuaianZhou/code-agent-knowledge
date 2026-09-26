import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.fixtures import nodes
from evaluation.harness import init_repo
from evaluation.on_demand import prepare


class OnDemandPreparation(unittest.TestCase):
    def test_store_available_without_preselected_context(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            init_repo(source, nodes())
            output = Path(prepare(root / "trials", source))
            experiment = json.loads((output / "experiment.json").read_text())
            self.assertEqual(set(experiment["run_order"]), {"export", "recovery", "inventory"})
            for name in experiment["run_order"]:
                trial = output / name
                request = json.loads((trial / "input/request.json").read_text())
                self.assertEqual(set(request), {"task", "project", "model", "max_output_tokens"})
                self.assertFalse((trial / "input/knowledge.json").exists())
                self.assertFalse((trial / "input/check.py").exists())
                self.assertTrue((trial / "workspace/knowledge/nodes").is_dir())
                skill = trial / "input/skills/knowledge-retrieve/SKILL.md"
                self.assertTrue(skill.is_file())
                self.assertFalse((trial / "input/skills/knowledge-extract").exists())
                policy = (trial / "workspace/project/AGENTS.md").read_text()
                self.assertIn("Choose queries from the task", policy)
                self.assertNotIn("{{", policy)
                self.assertNotIn("kn-", policy)
                self.assertIn("/input/skills/knowledge-retrieve/SKILL.md", policy)


if __name__ == "__main__":
    unittest.main()
