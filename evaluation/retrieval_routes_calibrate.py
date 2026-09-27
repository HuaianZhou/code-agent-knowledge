"""Measure semantic target ranks without involving an agent or changing fixtures."""
import argparse
from pathlib import Path

from knowledge_agent.index import Embedder, Index
from knowledge_agent.model import require
from .fulfillment import EMBEDDING
from .harness import dump, read


def calibrate(root):
    experiment = read(root / "experiment.json")
    index = Index(root / "calibration-index")
    embedder = Embedder(EMBEDDING)
    require(embedder.semantic, "Calibration requires a semantic embedding model")
    index.rebuild(root / experiment["run_order"][0] / "workspace/knowledge", "main", embedder)
    view = index.view()
    rows = []
    for case_id in experiment["run_order"]:
        case = read(root / case_id / "private.json")
        results = index.search(view, case["task"], embedder, limit=len(view.nodes), candidates=len(view.nodes), repo="orders")["results"]
        ids = [r["metadata"]["id"] for r in results]
        rows.append({"case": case_id, "query": case["task"], "ranked_ids": ids,
            "target_ranks": {t: ids.index(t) + 1 if t in ids else None for t in case["targets"]},
            "top3_recall": sum(t in ids[:3] for t in case["targets"]) / len(case["targets"]) if case["targets"] else None})
    return {"embedding": embedder.signature, "rows": rows,
        "note": "Task text queries; small seven-node synthetic corpus. Ranking calibration, not agent behavior. No-evidence intentionally has no target."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    path = args.directory / "calibration.json"
    require(not path.exists(), "Preserve existing calibration; use a fresh evaluation directory")
    dump(path, calibrate(args.directory))
    print(path)
