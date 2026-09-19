"""Strict versioned node schema and deterministic graph operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
import math
import re
import yaml


class KnowledgeError(ValueError):
    pass


STATUSES = {"active", "needs_review", "superseded", "archived"}
TYPES = {"constraint", "decision", "pitfall", "mechanism", "verification_rule"}
RELATIONS = {"constrained_by", "depends_on", "supported_by", "supersedes", "related_to"}
DEPENDENCIES = {"constrained_by", "depends_on", "supported_by"}
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise KnowledgeError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
# Preserve timestamps as strings so metadata is round-trippable through JSON.
UniqueLoader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in values if tag != "tag:yaml.org,2002:timestamp"]
    for k, values in UniqueLoader.yaml_implicit_resolvers.items()
}


def require(condition, message):
    if not condition:
        raise KnowledgeError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def safe_path(value):
    return (nonempty(value) and "\\" not in value and ":" not in value
            and not PurePosixPath(value).is_absolute()
            and all(part not in {"..", ".git"} for part in PurePosixPath(value).parts))


@dataclass
class Node:
    meta: dict
    body: str
    path: str = ""

    @property
    def id(self):
        return self.meta["id"]

    def markdown(self):
        return "---\n" + yaml.safe_dump(self.meta, sort_keys=False, allow_unicode=True) + "---\n\n" + self.body.strip() + "\n"

    def payload(self):
        # Policy v1: full concise body includes situation/conclusion/action/rationale.
        return "\n".join([self.meta["title"], self.meta["type"],
                          " ".join(self.meta["tags"]), self.body.strip()])

    def as_dict(self):
        return {"metadata": self.meta, "body": self.body, "path": self.path,
                "warning": "Knowledge requires review" if self.meta["status"] == "needs_review" else None}


def parse(text, path=""):
    lines = text.lstrip("\ufeff").splitlines()
    require(lines and lines[0] == "---", f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
        meta = yaml.load("\n".join(lines[1:end]), Loader=UniqueLoader)
    except (ValueError, yaml.YAMLError) as exc:
        raise KnowledgeError(f"{path}: invalid frontmatter: {exc}") from exc
    body = "\n".join(lines[end + 1:]).strip()
    validate_meta(meta, body)
    return Node(meta, body, path)


def validate_meta(m, body):
    require(isinstance(m, dict), "metadata must be a mapping")
    required = {"schema_version", "id", "title", "type", "tags", "weight", "status", "scope",
                "evidence_state", "anchors", "relations", "sources", "verification"}
    require(required <= m.keys(), f"missing fields: {sorted(required - m.keys())}")
    require(type(m["schema_version"]) is int and m["schema_version"] == 1, "unsupported schema_version")
    require(isinstance(m["id"], str) and bool(ID.fullmatch(m["id"])), "invalid stable ID")
    require(nonempty(m["title"]), "title is required")
    require(isinstance(m["type"], str) and m["type"] in TYPES, "invalid node type")
    require(isinstance(m["status"], str) and m["status"] in STATUSES, "invalid status")
    require(type(m["weight"]) in (float, int) and math.isfinite(m["weight"]) and 0 <= m["weight"] <= 1,
            "weight must be a finite number in [0, 1]")
    require(isinstance(m["tags"], list) and all(nonempty(t) for t in m["tags"]), "tags must be strings")
    require(isinstance(m["scope"], dict), "scope must be a mapping")
    for key in ("repositories", "conditions"):
        require(isinstance(m["scope"].get(key), list) and all(nonempty(t) for t in m["scope"][key]),
                f"scope.{key} must be a list of strings")
    require(isinstance(m["evidence_state"], str) and m["evidence_state"] in {"verified", "reported", "inferred"},
            "invalid evidence_state")
    require(nonempty(body), "node body is required")
    require(len(body) <= 24000, "body exceeds concise-node limit (24,000 characters); split coherent claims")
    for field in ("anchors", "relations", "sources"):
        require(isinstance(m[field], list) and all(isinstance(v, dict) for v in m[field]), f"invalid {field}")
    for a in m["anchors"]:
        require(nonempty(a.get("repo")) and safe_path(a.get("path")), "anchor requires repository and safe relative path")
        require(a.get("role") in ("evidence", "affected_code"), "invalid anchor role")
        require(isinstance(a.get("verified_commit"), str) and bool(SHA.fullmatch(a["verified_commit"])),
                "anchor requires full verified_commit SHA")
        require("symbol" not in a or nonempty(a["symbol"]), "anchor symbol must be nonempty")
    edges = set()
    for r in m["relations"]:
        require(isinstance(r.get("type"), str) and r["type"] in RELATIONS, "invalid relationship type")
        require(isinstance(r.get("target"), str) and bool(ID.fullmatch(r["target"])), "invalid relationship target")
        edge = (r["type"], r["target"])
        require(edge not in edges, "duplicate relationship")
        edges.add(edge)
    require(bool(m["sources"]), "at least one evidence source is required")
    for s in m["sources"]:
        require(s.get("kind") in ("test", "commit", "task", "human", "document", "experiment"), "invalid source kind")
        require(nonempty(s.get("reference")), "source reference is required")
    require(isinstance(m["verification"], dict), "verification must be a mapping")
    if m["evidence_state"] == "verified":
        require(all(nonempty(m["verification"].get(k)) for k in ("checked_at", "revision", "checked")),
                "verified evidence requires checked_at, revision and checked")
        try:
            datetime.fromisoformat(m["verification"]["checked_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise KnowledgeError("verification.checked_at must be ISO formatted") from exc


def validate_graph(nodes, aliases=None):
    aliases = aliases or {}
    for old in aliases:
        require(old not in nodes, f"alias collides with node: {old}")
        resolve(old, nodes, aliases)
    for n in nodes.values():
        for r in n.meta["relations"]:
            resolve(r["target"], nodes, aliases)


def resolve(node_id, nodes, aliases):
    seen = set()
    while node_id in aliases:
        require(node_id not in seen, "alias cycle")
        seen.add(node_id)
        node_id = aliases[node_id]
    require(node_id in nodes, f"dangling node reference: {node_id}")
    return node_id


def matches(n, types=(), tags=(), statuses=("active",), repo=None):
    m = n.meta
    return ((not types or m["type"] in types) and set(tags) <= set(m["tags"])
            and (not statuses or m["status"] in statuses)
            and (not repo or not m["scope"]["repositories"] or repo in m["scope"]["repositories"]))


def admission(decisions):
    require(isinstance(decisions, list), "admission decisions must be a list")
    seen = set()
    for d in decisions:
        require(isinstance(d, dict) and nonempty(d.get("id")), "admission decision needs an ID")
        require(d["id"] not in seen, "duplicate admission decision")
        seen.add(d["id"])
        for gate in ("not_cheaply_recoverable", "not_skill_duplicate", "actionable", "future_use"):
            item = d.get(gate)
            require(isinstance(item, dict) and item.get("passes") is True and nonempty(item.get("reason")),
                    f"{d['id']}: admission gate {gate} must pass with rationale")
        require(nonempty(d.get("existing_knowledge_search")), "document the existing knowledge search")
    return seen
