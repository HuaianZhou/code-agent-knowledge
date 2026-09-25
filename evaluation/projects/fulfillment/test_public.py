import io
import unittest
from wire_formats import decode
from exporter import write_batch
from recovery import replay_events, write_recovery


class PublicTests(unittest.TestCase):
    def test_explicit_formats(self):
        rows = [{"id": "s-1", "sku": "part,blue", "quantity": 2}]
        for fmt in ("csv-v1", "jsonl-v2"):
            out = io.StringIO()
            write_batch("example", rows, out, fmt)
            self.assertEqual(decode(io.StringIO(out.getvalue()), fmt), rows)

    def test_recovery_reduces_events(self):
        events = [{"op": "upsert", "id": "s-1", "sku": "x", "quantity": 2},
                  {"op": "upsert", "id": "s-1", "sku": "x", "quantity": 4},
                  {"op": "upsert", "id": "s-2", "sku": "y", "quantity": 1},
                  {"op": "delete", "id": "s-2"}]
        rows = [{"id": "s-1", "sku": "x", "quantity": 4}]
        self.assertEqual(replay_events(events), rows)
        out = io.StringIO()
        write_recovery("example", events, out, "jsonl-v2")
        self.assertEqual(decode(io.StringIO(out.getvalue()), "jsonl-v2"), rows)
