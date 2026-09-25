import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.task_end_trigger import prepare


class TriggerPreparation(unittest.TestCase):
    def test_capture_instruction_is_only_in_standing_policy(self):
        with TemporaryDirectory() as temp:
            root = Path(prepare(Path(temp) / "trials"))
            experiment = json.loads((root / "experiment.json").read_text())
            policies = []
            for tid in experiment["run_order"]:
                trial = root / tid
                request = json.loads((trial / "input/request.json").read_text())
                self.assertFalse({"cli", "skill", "applicable_skills", "result_contract"} & request.keys())
                self.assertNotIn("knowledge", json.dumps(request).lower())
                self.assertNotIn("capture", json.dumps(request).lower())
                policy = (trial / "workspace/project/AGENTS.md").read_text()
                policies.append(policy)
                self.assertIn("Before your final response", policy)
                self.assertNotIn("{{", policy)
                self.assertTrue((trial / "input/skills/knowledge-extract/SKILL.md").exists())
                self.assertTrue((trial / "grading/check.py").exists())
                self.assertFalse((trial / "input/private.json").exists())
            self.assertEqual(policies[0], policies[1])


if __name__ == "__main__":
    unittest.main()
