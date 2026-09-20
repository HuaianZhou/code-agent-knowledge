"""Read only committed snapshots; contribution writes are separate worktrees."""
from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess

from .model import KnowledgeError, parse, require, validate_graph, ID


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", str(repo), *map(str, args)], capture_output=True, encoding="utf-8")
    if check and result.returncode:
        raise KnowledgeError(result.stderr.strip() or result.stdout.strip())
    return result


def revision(repo, ref):
    require(not ref.startswith("-"), "invalid Git ref")
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.strip()


def snapshot(repo, ref):
    rev = revision(repo, ref)
    files = git(repo, "ls-tree", "-r", "-z", rev).stdout.split("\0")
    nodes, aliases = {}, {}
    for entry in files:
        if not entry:
            continue
        info, path = entry.split("\t", 1)
        mode, kind, oid = info.split()
        if not ((path.startswith("nodes/") and path.endswith(".md")) or path == "aliases.json"):
            continue
        require(mode == "100644" or mode == "100755", f"unsupported knowledge file type: {path}")
        text = git(repo, "cat-file", "blob", oid).stdout
        if path == "aliases.json":
            aliases = json.loads(text)
            require(isinstance(aliases, dict) and all(isinstance(k, str) and ID.fullmatch(k)
                    and isinstance(v, str) and ID.fullmatch(v) for k, v in aliases.items()), "invalid aliases.json")
        else:
            n = parse(text, path)
            require(n.id not in nodes, f"duplicate node ID: {n.id}")
            nodes[n.id] = n
    validate_graph(nodes, aliases)
    return rev, nodes, aliases


def config_path(path=None):
    return Path(path or os.environ.get("KNOWLEDGE_AGENT_CONFIG", Path.home() / ".knowledge-agent" / "config.json")).resolve()


def load_config(path=None):
    p = config_path(path)
    require(p.exists(), f"configuration missing: {p}; run setup")
    return json.loads(p.read_text(encoding="utf-8"))


def setup(config=None, repo=None, branch=None, name=None, email=None):
    """Create a private-to-this-machine knowledge store; never overwrite a directory."""
    p = config_path(config)
    if p.exists():
        data = load_config(p)
        require(repo is None or Path(repo).resolve() == Path(data["repo"]).resolve(),
                "configuration already points to another repository")
        require(branch is None or branch == data["branch"], "configuration already uses another branch")
        require(name is None and email is None, "setup does not change an existing Git identity")
        snapshot(data["repo"], accepted(data))
        return data, False
    target = Path(repo).resolve() if repo else p.parent / "knowledge"
    require(not target.exists(), "repository destination exists; use initialize for an existing repository")
    require(not p.is_relative_to(target), "configuration must be outside the knowledge repository")
    branch = branch or "main"
    require(not branch.startswith("-"), "invalid branch")
    target.parent.mkdir(parents=True, exist_ok=True)
    git(target.parent, "check-ref-format", "--branch", branch)
    require(name is None or bool(name.strip()), "name cannot be empty")
    require(email is None or bool(email.strip()), "email cannot be empty")
    target.mkdir()
    git(target, "init", "-b", branch)
    # A local application identity makes offline first use independent of GitHub.
    git(target, "config", "user.name", name or "Knowledge Agent")
    git(target, "config", "user.email", email or "knowledge-agent@localhost")
    (target / "nodes").mkdir()
    (target / "README.md").write_text(
        "# Local agent knowledge\n\nReviewed project knowledge lives in nodes/ as Markdown.\n"
        "This repository was created locally; no hosted account or remote is required.\n",
        encoding="utf-8")
    (target / "nodes" / ".gitkeep").write_text("", encoding="utf-8")
    (target / "aliases.json").write_text("{}\n", encoding="utf-8")
    git(target, "add", "--", "README.md", "nodes/.gitkeep", "aliases.json")
    git(target, "commit", "-m", "Initialize local agent knowledge")
    return initialize(p, target, branch=branch), True


def has_remote(config):
    return git(config["repo"], "remote", "get-url", "origin", check=False).returncode == 0


def initialize(config, repo, remote=None, branch="main", backend="lexical", model=None, model_revision=None):
    target = Path(repo).resolve()
    require(not branch.startswith("-"), "invalid branch")
    p = config_path(config)
    require(not p.exists(), "configuration already exists; edit it explicitly to change settings")
    require(backend in ("lexical", "sentence-transformers"), "unsupported embedding backend")
    if backend == "sentence-transformers":
        require(bool(model and model_revision), "semantic backend needs --model and --model-revision")
    if remote:
        require(not target.exists(), "clone destination already exists")
        require(not remote.startswith("-"), "invalid remote")
        target.parent.mkdir(parents=True, exist_ok=True)
        git(target.parent, "clone", "--branch", branch, "--", remote, target)
    else:
        revision(target, branch)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"repo": str(target), "branch": branch, "state": str(p.parent / "state"),
            "embedding": {"backend": backend, "model": model or "lexical-hash-v1", "revision": model_revision or "1"},
            "provider": None, "automatic_merge": False}
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def synchronize(config):
    repo, branch = config["repo"], config["branch"]
    old = accepted(config)
    if not has_remote(config):
        rev, _, _ = snapshot(repo, branch)
        return {"revision": rev, "stale": False, "mode": "local"}
    # Fetch does not touch the accepted checkout or unrelated local modifications.
    result = git(repo, "fetch", "origin", f"refs/heads/{branch}", check=False)
    if result.returncode:
        return {"revision": old, "stale": True, "warning": result.stderr.strip()}
    new = revision(repo, "FETCH_HEAD")
    require(git(repo, "merge-base", "--is-ancestor", old, new, check=False).returncode == 0,
            "accepted branch diverged; reconcile explicitly")
    # A private ref tracks remote acceptance; never reset a developer's branch.
    snapshot(repo, new)
    git(repo, "update-ref", "refs/knowledge-agent/accepted", new)
    return {"revision": new, "stale": False}


def accepted(config):
    if not has_remote(config):
        return revision(config["repo"], config["branch"])
    result = git(config["repo"], "rev-parse", "--verify", "refs/knowledge-agent/accepted", check=False)
    return result.stdout.strip() if result.returncode == 0 else revision(config["repo"], config["branch"])
