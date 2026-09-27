"""Run a held-out upstream behavioral regression against an isolated code copy.

The evaluator supplies the historical regression file, never the actor container.
This checks behavior through the local runtime and real SQLite/search services.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="basic-memory-grade-") as directory:
        project = Path(directory) / "project"
        shutil.copytree("/workspace/project", project,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv"))
        regression = "tests/index/test_local_project_index.py"
        shutil.copyfile("/grading/upstream_regression.py", project / regression)
        env = {**os.environ, "HOME": directory, "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([
            "/opt/basic-memory/bin/python", "-m", "pytest",
            regression + "::test_local_relation_resolution_refreshes_pending_source_without_markdown_file",
            "-q", "-o", "addopts=", "-p", "no:cacheprovider",
        ], cwd=project, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
