"""Private behavioral consumer checks. Never mounted in an agent container."""
import csv
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, "/workspace/project")
from exporter import write_batch
from recovery import write_recovery
from inventory import summarize

CONTRACT = json.loads(Path(__file__).with_name("contract.json").read_text())
ROWS = [{"id": "s-1", "sku": "blue,large", "quantity": 4},
        {"id": "s-2", "sku": "small", "quantity": 1}]


def consumer(payload, format_name):
    # Independent of agent-editable serializers/deserializers.
    if format_name == "csv-v1":
        reader = csv.DictReader(io.StringIO(payload))
        if reader.fieldnames != ["id", "sku", "quantity"]:
            raise ValueError("Deployed consumer rejects this header")
        return [{**r, "quantity": int(r["quantity"])} for r in reader]
    rows = [json.loads(line) for line in payload.splitlines() if line.strip()]
    if any(row.get("version") != 2 for row in rows):
        raise ValueError("Deployed consumer requires v2 records")
    return [{k: v for k, v in row.items() if k != "version"} for row in rows]


class DeploymentChecks(unittest.TestCase):
    def test_explicit_formats(self):
        for fmt in ("csv-v1", "jsonl-v2"):
            out = io.StringIO()
            write_batch("north", iter(ROWS), out, fmt)
            self.assertEqual(consumer(out.getvalue(), fmt), ROWS)

    def test_requested_behavior(self):
        task = CONTRACT["task"]
        if task == "inventory":
            self.assertEqual(summarize(iter(ROWS + [ROWS[0]])), {"blue,large": 8, "small": 1})
            self.assertEqual(summarize([]), {})
            for site in ("north", "south"):
                out = io.StringIO()
                write_batch(site, iter(ROWS), out)
                self.assertEqual(consumer(out.getvalue(), "csv-v1"), ROWS)
                out = io.StringIO()
                write_recovery(site, iter([{"op": "upsert", **r} for r in ROWS]), out)
                self.assertEqual(consumer(out.getvalue(), "csv-v1"), ROWS)
            return
        for site in ("north", "south", "new-site"):
            fmt = "csv-v1" if site == "north" and CONTRACT["era"] == "before" else "jsonl-v2"
            out = io.StringIO()
            if task == "export":
                write_batch(site, iter(ROWS), out)
            else:
                events = [{"op": "upsert", **r} for r in ROWS]
                events += [{"op": "upsert", "id": "discard", "sku": "x", "quantity": 10},
                           {"op": "delete", "id": "discard"}]
                write_recovery(site, iter(events), out)
            self.assertEqual(consumer(out.getvalue(), fmt), ROWS)


if __name__ == "__main__":
    unittest.main()
