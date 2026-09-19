"""Single-transaction snapshots; vector math is provided by sqlite-vec."""
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import json
import math
import re
import sqlite3

import sqlite_vec

from .gitstore import snapshot
from .model import KnowledgeError, Node, matches, require, resolve


class Embedder:
    def __init__(self, config):
        self.config = config
        self.semantic = config["backend"] == "sentence-transformers"
        if self.semantic:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise KnowledgeError("Install knowledge-agent[semantic] to use local semantic embeddings") from exc
            self.model = SentenceTransformer(config["model"], revision=config["revision"], trust_remote_code=False)
            self.dimensions = self.model.get_sentence_embedding_dimension()
        else:
            require(config["backend"] == "lexical", "unknown embedding backend")
            self.dimensions = 384

    @property
    def signature(self):
        return {**self.config, "dimensions": self.dimensions, "payload_policy": 1,
                "chunk_policy": "token-window-mean-v1" if self.semantic else "whole-node-v1",
                "distance": "cosine", "schema": 1}

    def encode(self, text):
        if self.semantic:
            # Token-aligned chunks avoid silently dropping a long node's action section.
            tokenizer = self.model.tokenizer
            tokens = tokenizer.encode(text, add_special_tokens=False)
            size = max(1, self.model.max_seq_length - 16)
            chunks = [tokenizer.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)] or [text]
            vectors = self.model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
            vector = vectors.mean(axis=0).tolist()
        else:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"\w+", text.lower()):
                digest = hashlib.sha256(token.encode()).digest()
                vector[int.from_bytes(digest[:4], "little") % self.dimensions] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(v * v for v in vector))
        require(norm > 0 and math.isfinite(norm), "embedding must be nonzero and finite")
        require(len(vector) == self.dimensions, "embedding dimension mismatch")
        return sqlite_vec.serialize_float32([v / norm for v in vector])


class Index:
    def __init__(self, state):
        self.path = Path(state) / "index.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=60)
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY, metadata TEXT NOT NULL, body TEXT NOT NULL, path TEXT NOT NULL, payload_hash TEXT NOT NULL, vector BLOB NOT NULL)")
        db.commit()
        return db

    def rebuild(self, repo, ref, embedder, force=False):
        rev, nodes, aliases = snapshot(repo, ref)
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            previous = dict(db.execute("SELECT key,value FROM state"))
            signature = json.dumps(embedder.signature, sort_keys=True)
            reset = force or previous.get("signature") != signature
            old = {} if reset else dict(db.execute("SELECT id,payload_hash FROM nodes"))
            if reset:
                db.execute("DELETE FROM nodes")
            embedded = 0
            for n in nodes.values():
                digest = hashlib.sha256(n.payload().encode()).hexdigest()
                if old.get(n.id) == digest:
                    db.execute("UPDATE nodes SET metadata=?,body=?,path=? WHERE id=?",
                               (json.dumps(n.meta), n.body, n.path, n.id))
                else:
                    vector = embedder.encode(n.payload())
                    db.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?)",
                               (n.id, json.dumps(n.meta), n.body, n.path, digest, vector))
                    embedded += 1
            deleted = set(old) - set(nodes)
            db.executemany("DELETE FROM nodes WHERE id=?", [(n,) for n in deleted])
            for k, v in {"revision": rev, "signature": signature, "aliases": json.dumps(aliases)}.items():
                db.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (k, v))
            db.commit()
            return {"revision": rev, "nodes": len(nodes), "embedded": embedded,
                    "deleted": len(deleted), "embedding": embedder.signature}
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def view(self, expected_revision=None):
        db = self.connect()
        try:
            db.execute("BEGIN")
            state = dict(db.execute("SELECT key,value FROM state"))
            require("revision" in state, "index missing; run rebuild-index")
            if expected_revision:
                require(expected_revision == state["revision"], "pinned revision differs from index; rebuild that revision")
            nodes = {r[0]: Node(json.loads(r[1]), r[2], r[3]) for r in db.execute("SELECT id,metadata,body,path FROM nodes")}
            vectors = dict(db.execute("SELECT id,vector FROM nodes"))
            return View(state["revision"], nodes, json.loads(state["aliases"]), json.loads(state["signature"]), vectors)
        finally:
            db.close()

    def search(self, view, query=None, embedder=None, order="relevance", limit=10, candidates=50,
               types=(), tags=(), statuses=("active",), repo=None):
        require(limit > 0 and candidates >= limit, "require 0 < limit <= candidates")
        require(order in ("relevance", "weight", "candidate-weight"), "invalid search ordering")
        require(query or order == "weight", "query required unless ordering globally by weight")
        pool = [n for n in view.nodes.values() if matches(n, types, tags, statuses, repo)]
        scores = {}
        if query:
            require(embedder is not None and view.signature == embedder.signature,
                    "incompatible embedding configuration; rebuild-index first")
            vector = embedder.encode(query)
            db = self.connect()
            try:
                # Exact scan over the filtered set; sqlite-vec implements vector distance.
                scores = {n.id: 1 - db.execute("SELECT vec_distance_cosine(?,?)", (view.vectors[n.id], vector)).fetchone()[0]
                          for n in pool}
            finally:
                db.close()
        if order == "weight":
            pool.sort(key=lambda n: (-n.meta["weight"], n.id))
            semantics = "global weight ordering over complete metadata-filtered set; query does not filter this set"
        else:
            pool.sort(key=lambda n: (-scores[n.id], n.id))
            pool = pool[:candidates]
            if order == "candidate-weight":
                pool.sort(key=lambda n: (-n.meta["weight"], -scores[n.id], n.id))
            semantics = f"{'semantic' if embedder.semantic else 'lexical (not semantic)'} top-{candidates} candidates, ordered by {order}"
        return {"revision": view.revision, "ordering": semantics, "embedding": view.signature,
                "results": [{**n.as_dict(), "score": scores.get(n.id)} for n in pool[:limit]]}


class View:
    def __init__(self, revision, nodes, aliases, signature, vectors):
        self.revision, self.nodes, self.aliases = revision, nodes, aliases
        self.signature, self.vectors = signature, vectors
        self.anchors = {}
        for n in nodes.values():
            for a in n.meta["anchors"]:
                self.anchors.setdefault((a["repo"], a["path"]), set()).add(n.id)

    def read(self, node_id):
        key = resolve(node_id, self.nodes, self.aliases)
        return {"revision": self.revision, "requested_id": node_id, "resolved_id": key, **self.nodes[key].as_dict()}

    def anchor(self, repo, path, symbol=None, statuses=("active",)):
        candidates = [self.nodes[key] for key in sorted(self.anchors.get((repo, path), set()))]
        return {"revision": self.revision, "results": [n.as_dict() for n in candidates
                if matches(n, statuses=statuses) and any(a["repo"] == repo and a["path"] == path
                and (not symbol or a.get("symbol") == symbol) for a in n.meta["anchors"])]}

    def context(self, node_id, depth=2, max_nodes=20, max_tokens=4000, direction="both",
                relations=(), statuses=("active",), repo=None):
        require(depth >= 0 and max_nodes > 0 and max_tokens > 0, "invalid traversal budgets")
        require(direction in ("in", "out", "both"), "invalid traversal direction")
        root = resolve(node_id, self.nodes, self.aliases)
        adjacency = {key: [] for key in self.nodes}
        for n in self.nodes.values():
            for r in n.meta["relations"]:
                if relations and r["type"] not in relations:
                    continue
                target = resolve(r["target"], self.nodes, self.aliases)
                edge = {"source": n.id, "target": target, "type": r["type"]}
                if direction in ("both", "out"):
                    adjacency[n.id].append((target, {**edge, "direction": "out"}))
                if direction in ("both", "in"):
                    adjacency[target].append((n.id, {**edge, "direction": "in"}))
        queue, seen, result, reasons, used = deque([(root, [])]), {root}, [], set(), 0
        while queue:
            key, path = queue.popleft()
            n = self.nodes[key]
            if not matches(n, statuses=statuses, repo=repo):
                continue
            item = {**n.as_dict(), "relationship_path": path}
            # UTF-8 byte count is a conservative token estimate, not model tokenization.
            cost = len(json.dumps(item, ensure_ascii=False).encode("utf-8"))
            if len(result) >= max_nodes:
                reasons.add("node_budget")
                continue
            if used + cost > max_tokens:
                reasons.add("token_budget")
                continue
            result.append(item)
            used += cost
            neighbors = sorted(adjacency[key], key=lambda pair: (pair[0], pair[1]["type"], pair[1]["direction"]))
            for neighbor, edge in neighbors:
                if neighbor in seen or not matches(self.nodes[neighbor], statuses=statuses, repo=repo):
                    continue
                if len(path) >= depth:
                    reasons.add("depth_limit")
                else:
                    seen.add(neighbor)
                    queue.append((neighbor, path + [edge]))
        return {"revision": self.revision, "results": result, "truncated": bool(reasons),
                "truncation_reasons": sorted(reasons), "estimated_tokens": used,
                "token_estimator": "conservative UTF-8 bytes of returned node records"}
