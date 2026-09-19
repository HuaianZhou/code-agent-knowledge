"""Agent proposals, review reports and non-destructive maintenance."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import uuid

from .gitstore import accepted, git, revision, snapshot, synchronize
from .model import DEPENDENCIES, KnowledgeError, admission, parse, require, resolve, validate_graph


def propose(config, manifest, manifest_dir=None):
    require(isinstance(manifest, dict), "proposal manifest must be an object")
    paths = manifest.get("nodes", [])
    require(isinstance(paths, list) and all(isinstance(p, str) for p in paths), "nodes must list Markdown paths")
    decisions = admission(manifest.get("admission", []))
    merges = manifest.get("merges", {})
    require(isinstance(merges, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in merges.items()),
            "merges must map retired IDs to surviving IDs")
    if not paths and not merges:
        require(not decisions, "admission decisions have no corresponding nodes")
        return {"outcome": "zero_qualifying_candidates", "writes": 0}
    base, nodes, aliases = snapshot(config["repo"], accepted(config))
    changed = {}
    for p in paths:
        path = (Path(manifest_dir or ".") / p).resolve()
        n = parse(path.read_text(encoding="utf-8"))
        require(n.id not in changed, f"duplicate proposed ID: {n.id}")
        require(n.id not in aliases, f"cannot reuse retired ID: {n.id}")
        changed[n.id] = n
    require(decisions == set(changed), "each supplied node needs exactly one admission declaration")
    for key, n in changed.items():
        n.path = nodes[key].path if key in nodes else f"nodes/{key}.md"
        nodes[key] = n
    removed = []
    for old, new in merges.items():
        require(old != new and old in nodes and new in nodes, "merge needs distinct existing node IDs")
        require(new in changed, "merge requires an admitted revised survivor node")
        retired, survivor = nodes[old], nodes[new]
        # Preserve documentary provenance even when the agent rewrites the conclusion.
        for source in retired.meta["sources"]:
            if source not in survivor.meta["sources"]:
                survivor.meta["sources"].append(source)
        for n in list(nodes.values()):
            rewritten = []
            for r in n.meta["relations"]:
                edge = {**r, "target": new if r["target"] == old else r["target"]}
                if edge["target"] != n.id and edge not in rewritten:
                    rewritten.append(edge)
            if rewritten != n.meta["relations"]:
                n.meta["relations"] = rewritten
                changed[n.id] = n
        for key, value in list(aliases.items()):
            if value == old:
                aliases[key] = new
        aliases[old] = new
        removed.append(retired.path)
        del nodes[old]
        changed.pop(old, None)
    validate_graph(nodes, aliases)
    ident = uuid.uuid4().hex[:12]
    branch = f"knowledge/proposal-{ident}"
    root = Path(config["state"]) / "proposals" / ident
    root.parent.mkdir(parents=True, exist_ok=True)
    git(config["repo"], "worktree", "add", "-b", branch, root, base)
    for special in (root / "aliases.json", root / "reviews", root / "nodes"):
        require(special.resolve().is_relative_to(root.resolve()), "unsafe proposal directory or file")
    # Stage exact generated paths only; accepted worktree is never modified.
    staged = []
    for n in changed.values():
        destination = root / n.path
        require(destination.resolve().is_relative_to(root.resolve()), "unsafe node destination")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(n.markdown(), encoding="utf-8")
        staged.append(n.path)
    for path in removed:
        (root / path).unlink()
        staged.append(path)
    (root / "aliases.json").write_text(json.dumps(aliases, indent=2) + "\n", encoding="utf-8")
    record_path = f"reviews/{ident}.json"
    record = {"id": ident, "base_revision": base, "created_at": datetime.now(timezone.utc).isoformat(),
              "admission": manifest.get("admission", []), "merges": merges,
              "semantic_review": "pending", "automatic_merge": False}
    (root / "reviews").mkdir(exist_ok=True)
    (root / record_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    git(root, "add", "--", *staged, "aliases.json", record_path)
    result = git(root, "commit", "-m", f"Propose knowledge {ident}", check=False)
    return {"outcome": "proposal", "branch": branch, "worktree": str(root), "base_revision": base,
            "committed": result.returncode == 0, "warning": result.stderr.strip() if result.returncode else None,
            "next": "Review against latest accepted state; push and open a request are separate operations."}


def review(config, branch, index, embedder):
    require(branch.startswith("knowledge/"), "review expects a knowledge contribution branch")
    has_remote = git(config["repo"], "remote", "get-url", "origin", check=False).returncode == 0
    sync = synchronize(config) if has_remote else {"revision": revision(config["repo"], config["branch"]), "stale": False}
    latest, current, aliases = snapshot(config["repo"], sync["revision"])
    proposed_rev, proposed, proposed_aliases = snapshot(config["repo"], branch)
    base = git(config["repo"], "merge-base", latest, proposed_rev).stdout.strip()
    _, before, _ = snapshot(config["repo"], base)
    changed = {key: n for key, n in proposed.items() if key not in before or n.markdown() != before[key].markdown()}
    conflicts = [key for key, n in changed.items() if key in before and key in current
                 and current[key].markdown() != before[key].markdown() and n.markdown() != current[key].markdown()]
    conflicts += [key for key in changed if key in before and key not in current]
    conflicts += [key for key in changed if key not in before and key in current
                  and changed[key].markdown() != current[key].markdown()]
    removed = set(before) - set(proposed)
    conflicts += [key for key in removed if key in current and before[key].markdown() != current[key].markdown()]
    combined = {key: value for key, value in current.items() if key not in removed}
    combined.update(changed)
    integrity = []
    try:
        validate_graph(combined, {**aliases, **proposed_aliases})
    except KnowledgeError as exc:
        integrity.append(str(exc))
    # Rebuild to the observed accepted commit before comparing proposals.
    index.rebuild(config["repo"], latest, embedder)
    view = index.view(latest)
    duplicates = []
    for n in changed.values():
        results = index.search(view, n.payload(), embedder, limit=6, candidates=6, statuses=())
        for candidate in results["results"]:
            meta = candidate["metadata"]
            if meta["id"] != n.id:
                duplicates.append({"proposed_id": n.id, "existing_id": meta["id"], "score": candidate["score"],
                                   "same_scope": meta["scope"] == n.meta["scope"],
                                   "proposed_scope": n.meta["scope"], "existing_scope": meta["scope"],
                                   "decision": "agent must compare conclusion, conditions, version and evidence"})
    return {"accepted_revision": latest, "proposal_revision": proposed_rev, "base_revision": base,
            "stale": sync["stale"], "warning": sync.get("warning"), "concurrent_changes": base != latest,
            "conflicting_ids": sorted(set(conflicts)), "integrity_errors": integrity,
            "duplicate_candidates": duplicates, "embedding": embedder.signature,
            "review_required": ["admission gates", "evidence", "scope and deployment", "skill overlap",
                                "semantic duplicates", "relationship meaning", "anchor correctness"],
            "merge_authorized": False,
            "recommendation": "blocked" if conflicts or integrity or sync["stale"] else "requires_agent_review",
            "note": "Rerun immediately before merge; this report is not merge authority."}


def review_impact(view, repo, paths=(), symbols=(), changed_ids=(), code_repo=None, base=None, head="HEAD"):
    moves, changed = {}, set(paths)
    if code_repo:
        require(base, "code diff requires a base revision")
        start, end = revision(code_repo, base), revision(code_repo, head)
        fields = git(code_repo, "diff", "--name-status", "-z", "-M", start, end, "--").stdout.split("\0")
        i = 0
        while i < len(fields) and fields[i]:
            status, path = fields[i], fields[i + 1]
            i += 2
            changed.add(path)
            if status.startswith(("R", "C")):
                new = fields[i]
                i += 1
                changed.add(new)
                moves[path] = new
    seeds = {resolve(key, view.nodes, view.aliases) for key in changed_ids}
    for n in view.nodes.values():
        if any(a["repo"] == repo and (a["path"] in changed or a.get("symbol") in symbols)
               for a in n.meta["anchors"]):
            seeds.add(n.id)
    incoming = {key: [] for key in view.nodes}
    for n in view.nodes.values():
        for r in n.meta["relations"]:
            if r["type"] in DEPENDENCIES:
                incoming[resolve(r["target"], view.nodes, view.aliases)].append(n.id)
    queue, reasons = deque(sorted(seeds)), {key: [key] for key in seeds}
    while queue:
        key = queue.popleft()
        for dependent in sorted(incoming[key]):
            if dependent not in reasons:
                reasons[dependent] = reasons[key] + [dependent]
                queue.append(dependent)
    return {"revision": view.revision, "changed_paths": sorted(changed), "suggested_anchor_moves": moves,
            "results": [{**view.nodes[key].as_dict(), "suggested_status": "needs_review", "impact_path": path}
                        for key, path in sorted(reasons.items())],
            "note": "Review candidates only. Code movement or changes do not prove a conclusion false."}


def maintenance(view, repositories, index=None, embedder=None):
    findings = []
    for n in view.nodes.values():
        for a in n.meta["anchors"]:
            location = repositories.get(a["repo"])
            if not location:
                findings.append({"id": n.id, "anchor": a, "reason": "repository not configured"})
                continue
            root = Path(location).resolve()
            target = (root / a["path"]).resolve()
            reason = None
            if not target.is_relative_to(root) or not target.is_file():
                reason = "missing or unsafe anchor path"
            elif git(root, "cat-file", "-e", a["verified_commit"] + "^{commit}", check=False).returncode:
                reason = "verified code revision unavailable"
            elif git(root, "diff", a["verified_commit"], "--", a["path"]).stdout:
                reason = "anchor changed since verified revision"
            elif a.get("symbol") and a["symbol"].split(".")[-1] not in target.read_text(encoding="utf-8", errors="replace"):
                reason = "symbol not found by lexical check; inspect manually"
            if reason:
                findings.append({"id": n.id, "anchor": a, "reason": reason, "suggested_status": "needs_review"})
    duplicates, seen = [], set()
    if index is not None and embedder is not None:
        for n in view.nodes.values():
            for candidate in index.search(view, n.payload(), embedder, limit=6, candidates=6, statuses=())["results"]:
                other = candidate["metadata"]
                pair = tuple(sorted((n.id, other["id"])))
                if n.id == other["id"] or pair in seen:
                    continue
                seen.add(pair)
                duplicates.append({"ids": list(pair), "score": candidate["score"],
                                   "same_scope": n.meta["scope"] == other["scope"],
                                   "decision": "candidate only; compare conclusions, conditions, versions and evidence"})
        duplicates.sort(key=lambda item: (-item["score"], item["ids"]))
    return {"revision": view.revision, "findings": findings, "duplicate_candidates": duplicates,
            "duplicate_scan": "completed" if index is not None else "not_requested",
            "note": "Unchanged code is not proof of validity. Review external conditions and deployment separately."}


def push(config, branch):
    require(branch.startswith("knowledge/"), "only knowledge contribution branches may be pushed")
    git(config["repo"], "check-ref-format", "--branch", branch)
    revision(config["repo"], branch)
    git(config["repo"], "push", "--set-upstream", "origin", f"{branch}:refs/heads/{branch}")
    return {"pushed": branch, "request_created": False}


def open_request(config, branch, title, body_file):
    require(branch.startswith("knowledge/"), "only knowledge contribution branches may open requests")
    provider = config.get("provider")
    require(provider in ("github", "gitlab"), "set provider to github or gitlab in configuration first")
    body = Path(body_file).read_text(encoding="utf-8")
    if provider == "github":
        cmd = ["gh", "pr", "create", "--draft", "--base", config["branch"], "--head", branch,
               "--title", title, "--body-file", str(Path(body_file).resolve())]
    else:
        cmd = ["glab", "mr", "create", "--draft", "--source-branch", branch, "--target-branch", config["branch"],
               "--title", title, "--description", body, "--yes"]
    result = subprocess.run(cmd, cwd=config["repo"], capture_output=True, text=True)
    require(result.returncode == 0, result.stderr)
    return {"provider": provider, "result": result.stdout.strip(), "merge_authorized": False}
