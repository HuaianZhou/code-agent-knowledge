"""Structured CLI. Every successful operation emits one JSON document."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .gitstore import accepted, config_path, initialize, load_config, setup, snapshot, synchronize
from .index import Embedder, Index
from .model import KnowledgeError, RELATIONS, STATUSES, TYPES, parse, require
from .workflow import accept_local, maintenance, open_request, propose, push, review, review_impact


def parser():
    p = argparse.ArgumentParser(description="Git-backed knowledge for coding agents")
    p.add_argument("--config", help="Persistent config path (or KNOWLEDGE_AGENT_CONFIG)")
    sub = p.add_subparsers(dest="command", required=True)
    local = sub.add_parser("setup", help="Create a local knowledge repository and index; no GitHub required")
    local.add_argument("--repo", help="Default: knowledge folder beside the config file")
    local.add_argument("--branch")
    local.add_argument("--name", help="Git author for the new repo; default: Knowledge Agent")
    local.add_argument("--email", help="Git author email for the new repo; default: knowledge-agent@localhost")
    init = sub.add_parser("initialize", help="Configure existing knowledge repo or clone a remote")
    init.add_argument("--repo", required=True)
    init.add_argument("--remote")
    init.add_argument("--branch", default="main")
    init.add_argument("--backend", choices=("lexical", "sentence-transformers"), default="lexical")
    init.add_argument("--model")
    init.add_argument("--model-revision")
    sub.add_parser("synchronize")
    rebuild = sub.add_parser("rebuild-index")
    rebuild.add_argument("--revision")
    rebuild.add_argument("--force", action="store_true")
    sub.add_parser("status")
    validate = sub.add_parser("validate")
    validate.add_argument("--revision")
    validate.add_argument("--file", help="Validate one uncommitted node's schema (links need snapshot validation)")
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?")
    search.add_argument("--order", choices=("relevance", "weight", "candidate-weight"), default="relevance")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--candidates", type=int, default=50)
    search.add_argument("--type", action="append", choices=sorted(TYPES), default=[])
    search.add_argument("--tag", action="append", default=[])
    search.add_argument("--repo")
    read = sub.add_parser("read")
    read.add_argument("id")
    context = sub.add_parser("context", aliases=["neighbors"])
    context.add_argument("id")
    context.add_argument("--depth", type=int, default=2)
    context.add_argument("--max-nodes", type=int, default=20)
    context.add_argument("--max-tokens", type=int, default=4000)
    context.add_argument("--direction", choices=("both", "in", "out"), default="both")
    context.add_argument("--relation", action="append", choices=sorted(RELATIONS), default=[])
    context.add_argument("--repo")
    anchor = sub.add_parser("lookup-anchor")
    anchor.add_argument("repo")
    anchor.add_argument("path")
    anchor.add_argument("--symbol")
    for command in (search, context, anchor):
        command.add_argument("--status", action="append", choices=sorted(STATUSES))
        command.add_argument("--all-statuses", action="store_true")
    for command in (search, read, context, anchor):
        command.add_argument("--revision", help="Require this exact indexed commit; fails on mismatch")
    proposal = sub.add_parser("propose", aliases=["task-end"])
    proposal.add_argument("manifest", help="JSON with node paths and admission declarations; empty list means zero writes")
    rev = sub.add_parser("review")
    rev.add_argument("branch")
    accept = sub.add_parser("accept", help="Explicitly accept a reviewed proposal in a local-only repository")
    accept.add_argument("branch")
    accept.add_argument("--reviewed-accepted", required=True, help="Full accepted_revision from review")
    accept.add_argument("--reviewed-proposal", required=True, help="Full proposal_revision from review")
    accept.add_argument("--reason", required=True, help="Review rationale, recorded in the merge commit")
    impact = sub.add_parser("review-impact")
    impact.add_argument("--repo", required=True)
    impact.add_argument("--path", action="append", default=[])
    impact.add_argument("--symbol", action="append", default=[])
    impact.add_argument("--changed-id", action="append", default=[])
    impact.add_argument("--code-repo")
    impact.add_argument("--base")
    impact.add_argument("--head", default="HEAD")
    maintain = sub.add_parser("maintain")
    maintain.add_argument("--repositories", help="JSON mapping repo identities to code checkout paths")
    maintain.add_argument("--duplicates", action="store_true", help="Include similarity candidates among accepted nodes")
    pub = sub.add_parser("push")
    pub.add_argument("branch")
    request = sub.add_parser("open-request")
    request.add_argument("branch")
    request.add_argument("--title", required=True)
    request.add_argument("--body-file", required=True)
    return p


def execute(args):
    if args.command == "setup":
        config, created = setup(args.config, args.repo, args.branch, args.name, args.email)
        result = Index(config["state"]).rebuild(config["repo"], accepted(config), Embedder(config["embedding"]))
        return {"config": str(config_path(args.config)), "repo": config["repo"], "created": created,
                "next": "Use task-end to propose nodes, review to inspect them, and accept after review.", **result}
    if args.command == "initialize":
        config = initialize(args.config, args.repo, args.remote, args.branch, args.backend, args.model, args.model_revision)
        result = Index(config["state"]).rebuild(config["repo"], accepted(config), Embedder(config["embedding"]))
        return {"config": str(config_path(args.config)), **result}
    if args.command == "validate" and args.file:
        n = parse(Path(args.file).read_text(encoding="utf-8"), args.file)
        return {"valid": True, "id": n.id, "scope": "single-node schema; graph links not checked"}
    config = load_config(args.config)
    index = Index(config["state"])
    if args.command == "synchronize":
        result = synchronize(config)
        indexed = index.rebuild(config["repo"], result["revision"], Embedder(config["embedding"]))
        return {**indexed, **result}
    if args.command == "rebuild-index":
        return index.rebuild(config["repo"], args.revision or accepted(config), Embedder(config["embedding"]), args.force)
    if args.command == "validate":
        rev, nodes, aliases = snapshot(config["repo"], args.revision or accepted(config))
        return {"valid": True, "revision": rev, "nodes": len(nodes), "aliases": len(aliases)}
    if args.command in ("propose", "task-end"):
        path = Path(args.manifest).resolve()
        return propose(config, json.loads(path.read_text(encoding="utf-8")), path.parent)
    if args.command == "review":
        return review(config, args.branch, index, Embedder(config["embedding"]))
    if args.command == "accept":
        # Load the model before changing Git, so an unavailable backend cannot cause a partial acceptance.
        embedder = Embedder(config["embedding"])
        result = accept_local(config, args.branch, args.reviewed_accepted, args.reviewed_proposal, args.reason)
        try:
            index.rebuild(config["repo"], result["revision"], embedder)
        except Exception as exc:
            return {**result, "indexed": False, "warning": f"Acceptance is committed; run rebuild-index: {exc}"}
        return {**result, "indexed": True}
    if args.command == "push":
        return push(config, args.branch)
    if args.command == "open-request":
        return open_request(config, args.branch, args.title, args.body_file)
    view = index.view(getattr(args, "revision", None))
    statuses = () if getattr(args, "all_statuses", False) else (getattr(args, "status", None) or ["active"])
    if args.command == "status":
        return {"indexed_revision": view.revision, "accepted_revision": accepted(config),
                "stale": view.revision != accepted(config), "nodes": len(view.nodes),
                "embedding": view.signature, "config": str(config_path(args.config)),
                "note": "Local refs only; synchronize to check remote freshness."}
    if args.command == "read":
        return view.read(args.id)
    if args.command == "search":
        return index.search(view, args.query, Embedder(config["embedding"]) if args.query else None,
                            args.order, args.limit, args.candidates, args.type, args.tag, statuses, args.repo)
    if args.command in ("context", "neighbors"):
        return view.context(args.id, args.depth, args.max_nodes, args.max_tokens,
                            args.direction, args.relation, statuses, args.repo)
    if args.command == "lookup-anchor":
        return view.anchor(args.repo, args.path, args.symbol, statuses)
    if args.command == "review-impact":
        return review_impact(view, args.repo, args.path, args.symbol, args.changed_id, args.code_repo, args.base, args.head)
    if args.command == "maintain":
        repos = json.loads(Path(args.repositories).read_text(encoding="utf-8")) if args.repositories else {}
        require(isinstance(repos, dict), "repositories must be a JSON object")
        return maintenance(view, repos, index if args.duplicates else None,
                           Embedder(config["embedding"]) if args.duplicates else None)
    raise KnowledgeError("unknown command")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        print(json.dumps(execute(args), ensure_ascii=False, indent=2))
        return 0
    except (KnowledgeError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
