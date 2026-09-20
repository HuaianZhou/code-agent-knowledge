from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import copy
import io
import json
import tempfile
import unittest

from knowledge_agent.cli import main
from knowledge_agent.gitstore import accepted, git, initialize, load_config, setup, snapshot, synchronize
from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import KnowledgeError, Node, parse, validate_graph
from knowledge_agent.workflow import accept_local, maintenance, propose, push, review, review_impact


def node(key, title=None, relations=(), weight=0.5, status="active", condition="v1"):
    return Node({"schema_version": 1, "id": key, "title": title or key, "type": "constraint",
                 "tags": ["persistence"], "weight": weight, "status": status,
                 "scope": {"repositories": ["orders"], "conditions": [condition]},
                 "evidence_state": "reported", "anchors": [],
                 "relations": [{"type": kind, "target": target} for kind, target in relations],
                 "sources": [{"kind": "human", "reference": "synthetic fixture correction"}], "verification": {}},
                "When changing persisted state encodings, migrate old journal records before changing the replay decoder.\n"
                "The reader and writer deploy independently; invalidate this guidance after the v2 migration.", f"nodes/{key}.md")


def declaration(key):
    return {"id": key, **{gate: {"passes": True, "reason": "Fixture-specific cross-module deployment constraint"}
                         for gate in ("not_cheaply_recoverable", "not_skill_duplicate", "actionable", "future_use")},
            "existing_knowledge_search": "Compared current nodes and their scope; fixture-only declaration"}


class KnowledgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "knowledge"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        self.a = node("A", "State encoder changes", [("constrained_by", "B")], .4)
        self.b = node("B", "Persisted ordinals outlive deployments", weight=.9)
        self.c = node("C", "Recovery tool changes", [("depends_on", "B")], .7)
        self.save(self.a, self.b, self.c)
        self.rev = self.commit()
        self.config = initialize(self.root / "config.json", self.repo)
        self.embed = Embedder(self.config["embedding"])
        self.index = Index(self.config["state"])
        self.index.rebuild(self.repo, "main", self.embed)

    def save(self, *nodes):
        for n in nodes:
            p = self.repo / n.path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(n.markdown(), encoding="utf-8")

    def commit(self):
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "Fixture change")
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def proposal(self, *nodes, merges=None):
        paths = []
        for n in nodes:
            p = self.root / f"{n.id}.md"
            p.write_text(n.markdown(), encoding="utf-8")
            paths.append(str(p))
        existing = snapshot(self.repo, accepted(self.config))[1]
        return propose(self.config, {"nodes": paths, "admission": [declaration(n.id) for n in nodes],
                                     "operations": {n.id: "update" if n.id in existing else "create" for n in nodes},
                                     "merges": merges or {}})

    def test_bidirectional_graph_and_cycles(self):
        self.b.meta["relations"] = [{"type": "depends_on", "target": "A"}]
        self.save(self.b)
        self.commit()
        self.index.rebuild(self.repo, "main", self.embed)
        context = self.index.view().context("A", max_tokens=100000)
        self.assertEqual([r["metadata"]["id"] for r in context["results"]], ["A", "B", "C"])
        self.assertEqual(context["results"][2]["relationship_path"][-1]["direction"], "in")
        self.assertFalse(context["truncated"])

    def test_budgets_and_direction(self):
        view = self.index.view()
        self.assertEqual(len(view.context("A", direction="out", max_tokens=100000)["results"]), 2)
        for kwargs, reason in [({"depth": 0}, "depth_limit"), ({"max_nodes": 1}, "node_budget"),
                               ({"max_tokens": 1}, "token_budget")]:
            report = view.context("A", **kwargs)
            self.assertTrue(report["truncated"])
            self.assertIn(reason, report["truncation_reasons"])

    def test_weight_filters_status_and_scope(self):
        self.b.meta["status"] = "needs_review"
        self.save(self.b)
        self.commit()
        self.index.rebuild(self.repo, "main", self.embed)
        view = self.index.view()
        results = self.index.search(view, order="weight")["results"]
        self.assertEqual([r["metadata"]["id"] for r in results], ["C", "A"])
        results = self.index.search(view, order="weight", statuses=())["results"]
        self.assertEqual(results[0]["metadata"]["id"], "B")
        self.assertTrue(results[0]["warning"])
        self.assertEqual(self.index.search(view, order="weight", repo="other")["results"], [])
        self.assertEqual(self.index.search(view, order="weight", tags=["missing"])["results"], [])

    def test_lexical_search_is_explicit(self):
        results = self.index.search(self.index.view(), "persisted ordinals", self.embed, limit=1)
        self.assertIn("not semantic", results["ordering"])
        self.assertEqual(results["results"][0]["metadata"]["id"], "B")
        results = self.index.search(self.index.view(), "encoder", self.embed, order="candidate-weight", limit=1, candidates=1)
        self.assertIn("top-1", results["ordering"])
        self.assertEqual(results["results"][0]["metadata"]["id"], "A")

    def test_renaming_and_metadata_only_updates(self):
        (self.repo / self.a.path).unlink()
        self.a.path = "nodes/moved.md"
        self.a.meta["weight"] = .99
        self.save(self.a)
        rev = self.commit()
        report = self.index.rebuild(self.repo, "main", self.embed)
        self.assertEqual(report["embedded"], 0)
        self.assertEqual(report["revision"], rev)
        self.assertEqual(self.index.view().read("A")["path"], "nodes/moved.md")
        self.assertEqual(len(self.index.view().context("C", max_tokens=100000)["results"]), 3)

    def test_incremental_delete_and_rebuild(self):
        (self.repo / self.c.path).unlink()
        self.a.body += " Verify migration compatibility."
        self.save(self.a)
        self.commit()
        report = self.index.rebuild(self.repo, "main", self.embed)
        self.assertEqual((report["embedded"], report["deleted"]), (1, 1))
        before = self.index.view()
        self.index.rebuild(self.repo, "main", self.embed, force=True)
        after = self.index.view()
        self.assertEqual(before.vectors, after.vectors)
        self.assertEqual(set(after.nodes), {"A", "B"})

    def test_interrupted_index_rolls_back(self):
        self.a.body += " changed"
        self.b.body += " changed"
        self.save(self.a, self.b)
        self.commit()
        real = self.embed.encode
        count = 0
        def fail(text):
            nonlocal count
            count += 1
            if count == 2:
                raise RuntimeError("simulated embedding failure")
            return real(text)
        self.embed.encode = fail
        with self.assertRaises(RuntimeError):
            self.index.rebuild(self.repo, "main", self.embed)
        self.assertEqual(self.index.view().revision, self.rev)
        self.assertNotIn("changed", self.index.view().nodes["A"].body)
        self.embed.encode = real
        self.index.rebuild(self.repo, "main", self.embed)
        self.assertIn("changed", self.index.view().nodes["A"].body)

    def test_concurrent_index_writers(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            reports = list(pool.map(lambda _: self.index.rebuild(self.repo, "main", self.embed), range(2)))
        self.assertTrue(all(r["revision"] == self.rev for r in reports))
        self.assertEqual(len(self.index.view().nodes), 3)

    def test_pin_and_incompatible_model(self):
        with self.assertRaises(KnowledgeError):
            self.index.view("bad-revision")
        self.embed.config = {**self.embed.config, "revision": "2"}
        with self.assertRaises(KnowledgeError):
            self.index.search(self.index.view(), "persisted", self.embed)
        self.assertEqual(self.index.rebuild(self.repo, "main", self.embed)["embedded"], 3)

    def test_zero_write_and_failed_admission(self):
        before = git(self.repo, "status", "--porcelain").stdout
        report = propose(self.config, {"nodes": [], "admission": []})
        self.assertEqual(report["writes"], 0)
        self.assertFalse((Path(self.config["state"]) / "proposals").exists())
        d = declaration("D")
        d["actionable"]["passes"] = False
        with self.assertRaises(KnowledgeError):
            propose(self.config, {"nodes": [], "admission": [d]})
        self.assertEqual(git(self.repo, "status", "--porcelain").stdout, before)

    def test_proposals_isolated_from_dirty_accepted_worktree(self):
        (self.repo / "unrelated.txt").write_text("keep me")
        report = self.proposal(node("D", relations=[("depends_on", "B")]))
        self.assertTrue(report["committed"])
        self.assertEqual((self.repo / "unrelated.txt").read_text(), "keep me")
        self.assertNotIn("D", snapshot(self.repo, "main")[1])
        self.assertIn("D", snapshot(self.repo, report["branch"])[1])

    def test_merge_redirects_and_provenance(self):
        d = node("D", "Migration guidance")
        d.meta["sources"] = [{"kind": "task", "reference": "new fixture task"}]
        report = self.proposal(d, merges={"B": "D"})
        _, nodes, aliases = snapshot(self.repo, report["branch"])
        self.assertEqual(aliases, {"B": "D"})
        self.assertNotIn("B", nodes)
        self.assertEqual(nodes["A"].meta["relations"][0]["target"], "D")
        self.assertEqual(len(nodes["D"].meta["sources"]), 2)
        self.index.rebuild(self.repo, report["branch"], self.embed)
        self.assertEqual(self.index.view().read("B")["resolved_id"], "D")

    def test_latest_review_catches_concurrent_semantic_candidate(self):
        report = self.proposal(node("D", "Migrate state before replay", condition="v2"))
        self.save(node("E", "Old journals survive deploys"))
        latest = self.commit()
        result = review(self.config, report["branch"], self.index, self.embed)
        self.assertEqual(result["accepted_revision"], latest)
        self.assertTrue(result["concurrent_changes"])
        candidates = [r for r in result["duplicate_candidates"] if r["existing_id"] == "E"]
        self.assertTrue(candidates)
        self.assertFalse(candidates[0]["same_scope"])
        self.assertFalse(result["merge_authorized"])

    def test_concurrent_same_id_conflict(self):
        update = copy.deepcopy(self.b)
        update.body += " Proposed update"
        report = self.proposal(update)
        self.b.body += " Accepted concurrent update"
        self.save(self.b)
        self.commit()
        result = review(self.config, report["branch"], self.index, self.embed)
        self.assertIn("B", result["conflicting_ids"])
        self.assertEqual(result["recommendation"], "blocked")

    def test_anchor_lookup_and_dependency_impact(self):
        self.b.meta["anchors"] = [{"repo": "orders", "path": "journal.py", "symbol": "decode",
                                    "role": "affected_code", "verified_commit": self.rev}]
        d = node("D", relations=[("related_to", "B")])
        self.save(self.b, d)
        self.commit()
        self.index.rebuild(self.repo, "main", self.embed)
        view = self.index.view()
        self.assertEqual(view.anchor("orders", "journal.py", "decode")["results"][0]["metadata"]["id"], "B")
        impact = review_impact(view, "orders", ["journal.py"])
        self.assertEqual({r["metadata"]["id"] for r in impact["results"]}, {"A", "B", "C"})
        self.assertTrue(all(r["suggested_status"] == "needs_review" for r in impact["results"]))
        self.assertTrue(all(n.meta["status"] == "active" for n in view.nodes.values()))

    def test_code_rename_and_maintenance(self):
        code = self.root / "code"
        code.mkdir()
        git(code, "init", "-b", "main")
        git(code, "config", "user.name", "Fixture")
        git(code, "config", "user.email", "fixture@example.invalid")
        (code / "journal.py").write_text("def decode():\n    return 1\n")
        git(code, "add", ".")
        git(code, "commit", "-m", "Initial")
        before = git(code, "rev-parse", "HEAD").stdout.strip()
        self.b.meta["anchors"] = [{"repo": "orders", "path": "journal.py", "symbol": "decode",
                                    "role": "evidence", "verified_commit": before}]
        self.save(self.b)
        self.commit()
        self.index.rebuild(self.repo, "main", self.embed)
        self.assertEqual(maintenance(self.index.view(), {"orders": str(code)})["findings"], [])
        git(code, "mv", "journal.py", "replay.py")
        git(code, "commit", "-m", "Move decoder")
        impact = review_impact(self.index.view(), "orders", code_repo=code, base=before)
        self.assertEqual(impact["suggested_anchor_moves"], {"journal.py": "replay.py"})
        self.assertEqual(len(maintenance(self.index.view(), {"orders": str(code)})["findings"]), 1)

    def test_remote_sync_and_dirty_local_preserved(self):
        bare = self.root / "remote.git"
        git(self.root, "clone", "--bare", self.repo, bare)
        clone = self.root / "reader"
        reader = initialize(self.root / "reader-config" / "config.json", clone, str(bare))
        (clone / "unrelated.txt").write_text("local work")
        self.save(node("D"))
        latest = self.commit()
        git(self.repo, "push", str(bare), "main")
        synced = synchronize(reader)
        self.assertFalse(synced["stale"])
        self.assertEqual(synced["revision"], latest)
        self.assertEqual((clone / "unrelated.txt").read_text(), "local work")
        self.assertEqual(git(clone, "rev-parse", "main").stdout.strip(), self.rev)
        idx = Index(reader["state"])
        idx.rebuild(clone, accepted(reader), self.embed)
        self.assertIn("D", idx.view().nodes)
        git(clone, "remote", "set-url", "origin", str(self.root / "missing.git"))
        offline = synchronize(reader)
        self.assertTrue(offline["stale"])
        self.assertEqual(offline["revision"], latest)

    def test_validation_rejects_invalid_nodes_and_links(self):
        for field, value in [("weight", float("nan")), ("status", "unknown"), ("sources", []), ("id", "../bad")]:
            n = copy.deepcopy(self.a)
            n.meta[field] = value
            with self.assertRaises(KnowledgeError):
                parse(n.markdown())
        with self.assertRaises(KnowledgeError):
            parse(self.a.markdown().replace("id: A", "id: A\nid: B"))
        with self.assertRaises(KnowledgeError):
            validate_graph({"A": self.a})
        with self.assertRaises(KnowledgeError):
            validate_graph({"A": self.a, "B": self.b}, {"X": "Y", "Y": "X"})

    def test_structured_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            result = main(["--config", str(self.root / "config.json"), "search", "--order", "weight"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(out.getvalue())["results"][0]["metadata"]["id"], "B")
        err = io.StringIO()
        with redirect_stderr(err):
            result = main(["--config", str(self.root / "config.json"), "read", "unknown"])
        self.assertEqual(result, 1)
        self.assertIn("error", json.loads(err.getvalue()))

    def test_invalid_snapshot_does_not_replace_index(self):
        self.a.meta["relations"].append({"type": "depends_on", "target": "missing"})
        self.save(self.a)
        # Dirty working files are not an accepted snapshot.
        self.assertEqual(self.index.rebuild(self.repo, "main", self.embed)["revision"], self.rev)
        self.commit()
        with self.assertRaises(KnowledgeError):
            self.index.rebuild(self.repo, "main", self.embed)
        self.assertEqual(self.index.view().revision, self.rev)

    def test_verified_evidence_requires_actual_verification_fields(self):
        n = copy.deepcopy(self.b)
        n.meta["evidence_state"] = "verified"
        with self.assertRaises(KnowledgeError):
            parse(n.markdown())
        n.meta["verification"] = {"checked_at": "not-a-date", "revision": self.rev, "checked": "fixture test"}
        with self.assertRaises(KnowledgeError):
            parse(n.markdown())
        n.meta["verification"]["checked_at"] = "2026-09-19T12:00:00Z"
        self.assertEqual(parse(n.markdown()).meta["evidence_state"], "verified")

    def test_maintenance_duplicate_candidates_are_not_merged(self):
        result = maintenance(self.index.view(), {}, self.index, self.embed)
        self.assertEqual(result["duplicate_scan"], "completed")
        self.assertTrue(result["duplicate_candidates"])
        pairs = [tuple(c["ids"]) for c in result["duplicate_candidates"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(set(self.index.view().nodes), {"A", "B", "C"})

    def test_initialize_does_not_clone_if_config_exists(self):
        target = self.root / "unexpected-clone"
        with self.assertRaises(KnowledgeError):
            initialize(self.root / "config.json", target, str(self.repo))
        self.assertFalse(target.exists())

    def test_proposal_rejects_missing_update_and_existing_create_before_writes(self):
        for key, operation in [("missing", "update"), ("B", "create")]:
            candidate = self.root / "candidate.md"
            candidate.write_text(node(key).markdown(), encoding="utf-8")
            manifest = {"nodes": [str(candidate)], "admission": [declaration(key)], "operations": {key: operation}}
            branches = git(self.repo, "branch", "--list").stdout
            with self.assertRaisesRegex(KnowledgeError, "cannot " + operation):
                propose(self.config, manifest)
            self.assertEqual(git(self.repo, "branch", "--list").stdout, branches)
            self.assertFalse((Path(self.config["state"]) / "proposals").exists())
            self.assertEqual(snapshot(self.repo, "main")[0], self.rev)

    def test_proposal_requires_explicit_operation_for_every_supplied_node(self):
        candidate = self.root / "candidate.md"
        candidate.write_text(self.b.markdown(), encoding="utf-8")
        for operations in ({}, {"B": "upsert"}, {"B": "update", "extra": "create"}):
            with self.assertRaises(KnowledgeError):
                propose(self.config, {"nodes": [str(candidate)], "admission": [declaration("B")], "operations": operations})
        with self.assertRaises(KnowledgeError):
            propose(self.config, {"nodes": [], "operations": {"B": "update"}})
        self.assertFalse((Path(self.config["state"]) / "proposals").exists())

    def test_explicit_update_preserves_existing_path_and_records_intent(self):
        (self.repo / self.b.path).unlink()
        self.b.path = "nodes/renamed-constraint.md"
        self.save(self.b)
        self.commit()
        revised = copy.deepcopy(self.b)
        revised.meta["title"] = "Updated constraint title"
        report = self.proposal(revised)
        _, nodes, _ = snapshot(self.repo, report["branch"])
        self.assertEqual(set(nodes), {"A", "B", "C"})
        self.assertEqual(nodes["B"].path, self.b.path)
        self.assertEqual(nodes["B"].meta["title"], revised.meta["title"])
        self.assertEqual(nodes["A"].meta["relations"][0]["target"], "B")
        record = next((Path(report["worktree"]) / "reviews").glob("*.json"))
        self.assertEqual(json.loads(record.read_text())["operations"], {"B": "update"})


    def test_setup_creates_local_repository_and_is_repeatable(self):
        path = self.root / "new-client" / "config.json"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--config", str(path), "setup"]), 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result["created"])
        config = load_config(path)
        self.assertEqual(git(config["repo"], "remote").stdout, "")
        self.assertEqual(git(config["repo"], "config", "user.email").stdout.strip(), "knowledge-agent@localhost")
        self.assertEqual(Index(config["state"]).view().nodes, {})
        before = path.read_bytes()
        again, created = setup(path)
        self.assertFalse(created)
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(synchronize(again), {"revision": result["revision"], "mode": "local", "stale": False})

    def test_setup_preserves_existing_directories_and_configuration(self):
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "keep.txt").write_text("user content")
        with self.assertRaises(KnowledgeError):
            setup(self.root / "new.json", existing)
        self.assertEqual((existing / "keep.txt").read_text(), "user content")
        with self.assertRaises(KnowledgeError):
            setup(self.root / "config.json", self.root / "different")
        self.assertFalse((self.root / "different").exists())

    def test_local_acceptance_refreshes_index_without_push(self):
        proposal = self.proposal(node("D", relations=[("depends_on", "B")]))
        report = review(self.config, proposal["branch"], self.index, self.embed)
        out = io.StringIO()
        with redirect_stdout(out):
            result = main(["--config", str(self.root / "config.json"), "accept", proposal["branch"],
                           "--reviewed-accepted", report["accepted_revision"],
                           "--reviewed-proposal", report["proposal_revision"], "--reason", "Fixture evidence reviewed"])
        self.assertEqual(result, 0)
        accepted_result = json.loads(out.getvalue())
        self.assertTrue(accepted_result["indexed"])
        self.assertFalse(accepted_result["pushed"])
        self.assertIn("D", self.index.view().nodes)
        self.assertEqual(self.index.view().revision, accepted(self.config))
        self.assertIn("Fixture evidence reviewed", git(self.repo, "log", "-1", "--format=%B").stdout)
        self.assertEqual(git(self.repo, "status", "--porcelain").stdout, "")

    def test_acceptance_rejects_stale_review_and_dirty_checkout(self):
        proposal = self.proposal(node("D"))
        proposed = snapshot(self.repo, proposal["branch"])[0]
        for old, new in [("wrong", proposed), (self.rev, "wrong")]:
            with self.assertRaisesRegex(KnowledgeError, "review is stale"):
                accept_local(self.config, proposal["branch"], old, new, "Reviewed")
        dirty = self.repo / "keep.txt"
        dirty.write_text("keep this work")
        with self.assertRaisesRegex(KnowledgeError, "uncommitted"):
            accept_local(self.config, proposal["branch"], self.rev, proposed, "Reviewed")
        self.assertEqual(dirty.read_text(), "keep this work")
        self.assertEqual(accepted(self.config), self.rev)
        self.assertFalse((self.repo / ".git" / "knowledge-agent-accept.lock").exists())

    def test_acceptance_serializes_and_rejects_remote_repository(self):
        proposal = self.proposal(node("D"))
        proposed = snapshot(self.repo, proposal["branch"])[0]
        lock = self.repo / ".git" / "knowledge-agent-accept.lock"
        lock.write_text("another reviewer")
        with self.assertRaisesRegex(KnowledgeError, "another acceptance"):
            accept_local(self.config, proposal["branch"], self.rev, proposed, "Reviewed")
        self.assertEqual(lock.read_text(), "another reviewer")
        lock.unlink()
        git(self.repo, "remote", "add", "origin", str(self.root / "remote.git"))
        with self.assertRaisesRegex(KnowledgeError, "local repositories"):
            accept_local(self.config, proposal["branch"], self.rev, proposed, "Reviewed")
        self.assertEqual(accepted(self.config), self.rev)

    def test_local_push_explains_local_acceptance(self):
        with self.assertRaisesRegex(KnowledgeError, "use review and accept"):
            push(self.config, "knowledge/proposal-missing")

    def test_acceptance_rejects_concurrent_accepted_changes(self):
        proposal = self.proposal(node("D"))
        proposed = snapshot(self.repo, proposal["branch"])[0]
        self.save(node("E"))
        current = self.commit()
        with self.assertRaisesRegex(KnowledgeError, "review is stale"):
            accept_local(self.config, proposal["branch"], self.rev, proposed, "Old review")
        with self.assertRaisesRegex(KnowledgeError, "older accepted knowledge"):
            accept_local(self.config, proposal["branch"], current, proposed, "Re-review without reconciliation")
        self.assertEqual(accepted(self.config), current)


if __name__ == "__main__":
    unittest.main()
