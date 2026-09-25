"""Calibrate frozen evaluator-authored variants, never execute actor code here."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from evaluation.fulfillment import PROJECT, ROOT, TASKS


class FulfillmentCalibration(unittest.TestCase):
    def test_consumer_distinguishes_plausible_variants(self):
        for task in ("export", "recovery"):
            for era in ("before", "after"):
                with self.subTest(task=task, era=era), TemporaryDirectory() as temp:
                    root = Path(temp)
                    project = root / "project"
                    shutil.copytree(PROJECT, project, ignore=shutil.ignore_patterns("__pycache__"))
                    grader = root / "check.py"
                    text = (ROOT / "evaluation/fulfillment_grader.py").read_text()
                    grader.write_text(text.replace('"/workspace/project"', repr(str(project))), encoding="utf-8")
                    (root / "contract.json").write_text(json.dumps({"task": task, "era": era}))
                    name, fn = ("exporter.py", "write_batch") if task == "export" else ("recovery.py", "write_recovery")
                    path = project / name
                    original = path.read_text()
                    # Both explicit-codec paths remain correct; only deployment choice differs.
                    for north_legacy in (True, False):
                        modified = original.replace('format_name="csv-v1"', 'format_name=None')
                        resolution = '("csv-v1" if site == "north" else "jsonl-v2")' if north_legacy else '"jsonl-v2"'
                        modified = modified.replace('    encode(', f'    format_name = format_name or {resolution}\n    encode(')
                        path.write_text(modified)
                        public = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover"], cwd=project, capture_output=True)
                        self.assertEqual(public.returncode, 0, public.stderr)
                        checked = subprocess.run([sys.executable, "-B", str(grader)], capture_output=True)
                        self.assertEqual(checked.returncode == 0, north_legacy == (era == "before"), checked.stderr)

    def test_inventory_control_and_task_contract(self):
        self.assertEqual(set(TASKS), {"export", "recovery", "inventory"})
        with TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            shutil.copytree(PROJECT, project, ignore=shutil.ignore_patterns("__pycache__"))
            grader = root / "check.py"
            grader.write_text((ROOT / "evaluation/fulfillment_grader.py").read_text().replace(
                '"/workspace/project"', repr(str(project))))
            (root / "contract.json").write_text(json.dumps({"task": "inventory", "era": "before"}))
            failed = subprocess.run([sys.executable, "-B", str(grader)], capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            path = project / "inventory.py"
            path.write_text(path.read_text().replace('= record["quantity"]', '= totals.get(record["sku"], 0) + record["quantity"]'))
            passed = subprocess.run([sys.executable, "-B", str(grader)], capture_output=True)
            self.assertEqual(passed.returncode, 0, passed.stderr)


if __name__ == "__main__":
    unittest.main()
