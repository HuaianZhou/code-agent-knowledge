"""Run one frozen coding batch sequentially; retain behavioral failures."""
import argparse
import json
from pathlib import Path

from .harness import read, run_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--codex-auth", required=True)
    args = parser.parse_args()
    experiment = read(args.directory / "experiment.json")
    for tid in experiment["run_order"]:
        trial = args.directory / tid
        print("Starting " + tid, flush=True)
        actor = run_trial(trial, args.image, timeout=600, network="bridge",
                          env_file=args.env_file, codex_auth=args.codex_auth)
        print(json.dumps({"trial": tid, "actor": actor}), flush=True)
        if actor["exit_code"]:
            print("Stopped on unsuccessful actor execution; preserve attempt and inspect trace.", flush=True)
            return 1
        grader = run_trial(trial, args.image, timeout=120, grading=True)
        print(json.dumps({"trial": tid, "grader": grader}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
