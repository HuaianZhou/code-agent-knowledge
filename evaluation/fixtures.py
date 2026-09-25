"""Synthetic inputs. Expected answers stay in the evaluator, never agent bundles."""
from pathlib import Path
import json

from knowledge_agent.model import Node


PROJECT = {
    "writer.py": 'from enum import IntEnum\nimport json\n\nclass State(IntEnum):\n    NEW = 0\n    PAID = 1\n    CANCELLED = 2\n\ndef append_order(stream, order_id, state):\n    stream.write(json.dumps({"id": order_id, "state": int(state)}) + "\\n")\n',
    "recovery.py": 'import json\n\ndef replay(stream):\n    return [(row["id"], {0: "new", 1: "paid", 2: "cancelled"}[row["state"]])\n            for row in map(json.loads, stream)]\n',
    "README.md": "# Orders fixture\nThe writer emits JSON lines; recovery reads them. Run tests with python -m unittest discover.\n",
    "test_public.py": 'import io, unittest\nfrom writer import State, append_order\nfrom recovery import replay\n\nclass PublicTest(unittest.TestCase):\n    def test_current_roundtrip(self):\n        stream = io.StringIO()\n        append_order(stream, "x", State.PAID)\n        stream.seek(0)\n        self.assertEqual(replay(stream), [("x", "paid")])\n'
}

CLAIMS = {
    "kn-retained-format": ("Stable ordinals across independent deployments", "constraint", .95, [],
        "For unversioned retained journals, preserve NEW=0, PAID=1 and CANCELLED=2 when adding states. "
        "A separately deployed recovery appliance reads archives for seven years; a writer rollout does not update it or migrate old data. "
        "Coordinate migrations and reader deployment before changing numeric meanings. Human operations guidance establishes this condition. "
        "Reassess once every supported reader and retained archive uses a versioned migrated format."),
    "kn-writer-evolution": ("Order lifecycle feature implementation", "decision", .7, [("related_nodes", "kn-retained-format")],
        "When adding an order lifecycle state, choose its numeric representation using the retained-format constraint and test current and historical records."),
    "kn-recovery-check": ("Replay verification for export changes", "verification_rule", .8, [("related_nodes", "kn-retained-format")],
        "For export and replay changes, test retained journals against supported recovery readers. Verify compatibility before rollout; do not infer deployment from a code merge."),
    "kn-logging": ("Drain diagnostic queues at shutdown", "pitfall", .6, [],
        "During process shutdown, drain queued diagnostics before terminating the consumer, or the diagnostic tail can be lost. Recheck when logging becomes synchronous."),
    "kn-timeout": ("Resolve ambiguous payment outcomes", "decision", .9, [],
        "For the legacy non-idempotent endpoint, query transaction status after a timeout before resubmitting a charge. A lost response is not proof of failure."),
    "kn-cache": ("Tenant-aware memoization boundaries", "constraint", .8, [],
        "Include tenant identity in cache keys for shared workers. Otherwise the same resource ID in two tenants can leak one tenant's cached result to another."),
    "kn-clock": ("Elapsed-time checks use monotonic readings", "verification_rule", .6, [],
        "Measure retry deadlines with a monotonic clock because wall-clock adjustments can otherwise extend or prematurely end timeouts."),
    "kn-schema": ("Two-phase database column removal", "mechanism", .75, [],
        "Stop all supported application versions reading a database column before dropping it. Rolling deployment temporarily leaves old and new binaries running together.")
}

QUERIES = [
    ("kn-retained-format", "Can I renumber persisted status values if the restoration appliance is upgraded later?"),
    ("kn-retained-format", "Why could old order backups be interpreted incorrectly after a service rollout?"),
    ("kn-logging", "How do I avoid losing the last diagnostic messages when a process exits?"),
    ("kn-logging", "The final log events disappear when the consumer stops. What must finish first?"),
    ("kn-timeout", "The bank never answered our request; is sending the charge again safe?"),
    ("kn-timeout", "A response was lost after submitting money. How do we prevent billing twice?"),
    ("kn-cache", "Two customers have identical object IDs in a shared worker. What belongs in the lookup key?"),
    ("kn-cache", "How can we stop one customer's stored results appearing for another customer?"),
    ("kn-clock", "System time jumped backwards and our retry deadline changed. Which timer should we use?"),
    ("kn-schema", "When can a field be deleted while older application instances are still serving requests?")
]


def nodes():
    result = {}
    for key, (title, kind, weight, relations, body) in CLAIMS.items():
        result[key] = Node({"schema_version": 1, "id": key, "title": title, "type": kind,
                           "tags": ["fixture"], "weight": weight, "status": "active",
                           "scope": {"repositories": ["orders"], "conditions": ["synthetic evaluation"]},
                           "evidence_state": "reported", "anchors": [],
                           "relations": [{"type": t, "target": k} for t, k in relations],
                           "sources": [{"kind": "human", "reference": "synthetic operations guidance for evaluation"}],
                           "verification": {}}, body, f"nodes/{key}.md")
    return result


def cases():
    return json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))["cases"]


def write_project(path):
    path.mkdir(parents=True, exist_ok=True)
    for name, content in PROJECT.items():
        (path / name).write_text(content, encoding="utf-8")
