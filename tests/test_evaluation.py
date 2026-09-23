from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest

from evaluation.fixtures import cases, nodes, write_project
from evaluation.harness import (container_command, controlled_contexts, dump, init_repo, prepare_capture,
                                prepare_reuse, read, retrieval_report, score_capture, summarize_reuse, GRADE)
from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import KnowledgeError


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def index(self):
        repo = self.root / "repo"
        init_repo(repo, nodes())
        embedder = Embedder({"backend": "lexical", "model": "lexical-hash-v1", "revision": "1"})
        index = Index(self.root / "index")
        index.rebuild(repo, "main", embedder)
        return index, embedder

    def test_lexical_results_cannot_pass_semantic_evaluation(self):
        index, embedder = self.index()
        with self.assertRaisesRegex(KnowledgeError, "lexical"):
            retrieval_report(index, index.view(), embedder)
        diagnostic = retrieval_report(index, index.view(), embedder, require_semantic=False)
        self.assertIsNone(diagnostic["passed"])
        self.assertEqual(len(diagnostic["queries"]), 10)
        self.assertTrue(0 <= diagnostic["recall_at_k"] <= 1)
        with self.assertRaises(KnowledgeError):
            retrieval_report(index, index.view(), embedder, k=len(nodes()), require_semantic=False)

    def test_capture_requires_explicit_embedding_and_preserves_pin(self):
        root = self.root / "semantic-capture"
        with self.assertRaisesRegex(KnowledgeError, "embedding model"):
            prepare_capture(root, "agent-model")
        self.assertFalse(root.exists())
        pin = "a" * 40
        prepare_capture(root, "agent-model", "example/model", pin)
        for case in cases():
            config = read(root / case["id"] / "workspace" / "config.json")
            self.assertEqual(config["embedding"], {
                "backend": "sentence-transformers", "model": "example/model", "revision": pin})
            self.assertEqual(read(root / case["id"] / "private.json")["embedding"], config["embedding"])
        with self.assertRaises(KnowledgeError):
            prepare_reuse(self.root / "invalid", "agent-model", embedding_model="example/model",
                          embedding_revision="main")

    def test_controlled_context_has_shared_entry_and_equal_budget(self):
        index, embedder = self.index()
        contexts, seed = controlled_contexts(index, embedder, 2400)
        self.assertEqual(contexts["none"]["results"], [])
        for condition in ("flat", "graph"):
            self.assertEqual(contexts[condition]["results"][0]["metadata"]["id"], seed)
            self.assertLessEqual(contexts[condition]["estimated_tokens"], 2400)
        all_context, _ = controlled_contexts(index, embedder, 20000)
        self.assertEqual({n["metadata"]["id"] for n in all_context["graph"]["results"]},
                         {"kn-writer-evolution", "kn-retained-format", "kn-recovery-check"})

    def test_reuse_preparation_and_pending_summary(self):
        root = self.root / "reuse"
        prepared = prepare_reuse(root, "fixture-model-v1", repeats=2, lexical_diagnostic=True)
        self.assertEqual(len(prepared["run_order"]), 6)
        snapshots = []
        for trial_id in prepared["run_order"]:
            trial = root / trial_id
            snapshots.append(read(trial / "private.json")["starting_files"])
            self.assertFalse((trial / "input" / "check.py").exists())
            self.assertTrue((trial / "grading" / "check.py").exists())
            agent_cmd = container_command(trial, "fixture-image")
            self.assertNotIn(str(trial / "grading"), " ".join(agent_cmd))
            self.assertNotIn(str(trial / "private.json"), " ".join(agent_cmd))
            grade_cmd = container_command(trial, "fixture-image", grading=True)
            self.assertNotIn(str(trial / "input"), " ".join(grade_cmd))
            self.assertIn("--network=none", grade_cmd)
            auth = self.root / "test-auth.json"
            auth.write_text("{}", encoding="utf-8")
            with_auth = container_command(trial, "fixture-image", codex_auth=auth)
            self.assertIn(f"type=bind,source={auth.resolve()},target=/run/codex-auth.json,readonly", with_auth)
            self.assertNotIn("/run/codex-auth.json", " ".join(container_command(
                trial, "fixture-image", grading=True, codex_auth=auth)))
        self.assertTrue(all(s == snapshots[0] for s in snapshots))
        summary = summarize_reuse(root)
        self.assertTrue(all(t["status"] == "pending" for t in summary["trials"]))
        self.assertIsNone(summary["adoption_conclusion"])
        with self.assertRaises(KnowledgeError):
            prepare_reuse(root, "fixture-model-v1", lexical_diagnostic=True)

    def test_capture_gold_is_not_exported_and_claimed_success_not_trusted(self):
        root = self.root / "capture"
        prepared = prepare_capture(root, "fixture-model-v1", lexical_diagnostic=True)
        self.assertEqual(prepared["cases"], len(cases()))
        for case in cases():
            request = read(root / case["id"] / "input" / "request.json")
            self.assertNotIn("expected", request)
            self.assertNotIn("rubric", request)
            self.assertNotIn(case["rubric"], json.dumps(request))
        trial = root / "implicit_constraint"
        dump(trial / "output" / "result.json", {"outcome": "zero_qualifying_candidates"})
        score = score_capture(trial)
        self.assertEqual(score["status"], "unverified_run")
        self.assertTrue(score["contract_errors"])
        zero = root / "zero_value"
        dump(zero / "output" / "result.json", {"outcome": "zero_qualifying_candidates", "model": "fixture-model-v1"})
        dump(zero / "run.json", {"exit_code": 0, "isolation": "test-fixture-only"})
        self.assertEqual(score_capture(zero)["status"], "needs_semantic_review")
        card = self.root / "scorecard.json"
        dump(card, {"reviewer": "fixture reviewer", **{key: {"passes": True, "evidence": "fixture-only rubric exercise"}
                   for key in ("admission", "evidence", "reuse", "relationships", "scope")}})
        self.assertEqual(score_capture(zero, card)["status"], "passed")

    def test_summary_does_not_accept_self_reported_success(self):
        root = self.root / "reuse"
        experiment = prepare_reuse(root, "model-v1", repeats=1, lexical_diagnostic=True)
        trial = root / experiment["run_order"][0]
        dump(trial / "output" / "result.json", {"model": "model-v1", "success": True})
        dump(trial / "run.json", {"exit_code": 0, "wall_seconds": 1})
        self.assertEqual(summarize_reuse(root)["trials"][0]["status"], "needs_grading")
        dump(trial / "grading-run.json", {"exit_code": 1})
        self.assertEqual(summarize_reuse(root)["trials"][0]["status"], "failed")
        dump(trial / "output" / "result.json", {"model": "wrong-model"})
        self.assertEqual(summarize_reuse(root)["trials"][0]["status"], "invalid_run")

    def test_grader_rejects_renumbering_and_accepts_compatible_feature(self):
        # Trusted evaluator-authored fixtures only. Agent-written code is graded in Docker.
        project = self.root / "project"
        write_project(project)
        grader = self.root / "grader.py"
        grader.write_text(GRADE.replace('"/workspace/project"', repr(str(project))))
        initial = subprocess.run([sys.executable, str(grader)], capture_output=True)
        self.assertNotEqual(initial.returncode, 0)
        writer = project / "writer.py"
        recovery = project / "recovery.py"
        writer.write_text(writer.read_text().replace("    CANCELLED = 2", "    CANCELLED = 2\n    REFUNDED = 3"))
        recovery.write_text(recovery.read_text().replace('2: "cancelled"', '2: "cancelled", 3: "refunded"'))
        correct = subprocess.run([sys.executable, "-B", str(grader)], capture_output=True)
        self.assertEqual(correct.returncode, 0, correct.stderr)
        writer.write_text(writer.read_text().replace("CANCELLED = 2", "CANCELLED = 30"))
        wrong = subprocess.run([sys.executable, "-B", str(grader)], capture_output=True)
        self.assertNotEqual(wrong.returncode, 0)


if __name__ == "__main__":
    unittest.main()
