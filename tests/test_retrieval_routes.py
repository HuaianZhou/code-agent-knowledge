from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from evaluation.harness import init_repo, container_command
from evaluation.retrieval_routes import CASES, corpus, prepare
from evaluation.retrieval_routes_report import report
from knowledge_agent.gitstore import initialize
from knowledge_agent.index import Embedder, Index


class RetrievalRoutes(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def indexed(self):
        repo = self.root / "knowledge"
        init_repo(repo, corpus("a" * 40))
        config = initialize(self.root / "config.json", repo)
        embedder = Embedder(config["embedding"])
        index = Index(config["state"])
        index.rebuild(repo, "main", embedder)
        return index, index.view(), embedder

    def test_metadata_empty_weak_and_wrong_type_are_distinct(self):
        index, view, _ = self.indexed()
        def browse(**filters):
            return {r["metadata"]["id"] for r in index.search(view, order="weight", **filters)["results"]}
        self.assertEqual(browse(tags=["storage"]), {"kn-archive"})
        self.assertEqual(browse(tags=["retries"]), set())
        self.assertEqual(browse(tags=["retry"]), {"kn-timer"})
        self.assertNotIn("kn-partner", browse(tags=["retry"]))
        self.assertNotIn("kn-cache", browse(types=["decision"]))
        self.assertIn("kn-cache", browse())

    def test_body_payload_and_anchor_graph_paths(self):
        _, view, _ = self.indexed()
        partner = view.nodes["kn-partner"]
        self.assertNotIn("idempotency", partner.meta["title"])
        self.assertIn("idempotency", partner.payload())
        self.assertEqual({r["metadata"]["id"] for r in view.anchor("orders", "writer.py")["results"]}, {"kn-writer"})
        self.assertEqual(view.anchor("other-repo", "writer.py")["results"], [])
        report = view.context("kn-writer", depth=2, max_tokens=20000)
        ids = {r["metadata"]["id"] for r in report["results"]}
        self.assertEqual(ids, {"kn-writer", "kn-archive", "kn-restoration"})
        self.assertFalse(report["truncated"])

    def test_preparation_hides_rubrics_and_uses_dedicated_skill(self):
        root = Path(prepare(self.root / "trials"))
        for name, case in CASES.items():
            trial = root / name
            request = json.loads((trial / "input/request.json").read_text())
            self.assertEqual(set(request), {"task", "project", "model", "max_output_tokens"})
            self.assertNotIn(case["criterion"], json.dumps(request))
            self.assertFalse((trial / "input/private.json").exists())
            self.assertFalse((trial / "input/knowledge.json").exists())
            self.assertTrue((trial / "input/skills/knowledge-retrieve/SKILL.md").is_file())
            self.assertFalse((trial / "input/skills/knowledge-extract").exists())
            mounts = " ".join(container_command(trial, "test-image"))
            self.assertNotIn(str(trial / "private.json"), mounts)
            self.assertNotIn("source=" + str(trial) + ",", mounts)
        # A successful actor exit or its own claim is not a semantic grade.
        trial = root / "metadata_hit"
        (trial / "run.json").write_text(json.dumps({"exit_code": 0}))
        (trial / "output/result.json").write_text(json.dumps({"model": "gpt-6-astra", "success": True}))
        self.assertEqual(report(root)["trials"][0]["status"], "needs_review")
        (trial / "reviewer.json").write_text(json.dumps({"answer_supported": False, "no_writes": True}))
        self.assertEqual(report(root)["trials"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
