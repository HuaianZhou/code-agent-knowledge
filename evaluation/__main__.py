import argparse
import json
import sys

from knowledge_agent.model import KnowledgeError
from .harness import prepare_capture, prepare_reuse, run_trial, score_capture, semantic_eval, summarize_reuse


def main(argv=None):
    parser = argparse.ArgumentParser(description="Three-layer knowledge-agent evaluation")
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("prepare-capture")
    capture.add_argument("--output", required=True)
    capture.add_argument("--model", required=True)
    semantic = sub.add_parser("retrieval")
    semantic.add_argument("--output", required=True)
    semantic.add_argument("--model")
    semantic.add_argument("--revision")
    semantic.add_argument("--k", type=int, default=3)
    semantic.add_argument("--threshold", type=float, default=.8)
    semantic.add_argument("--lexical-diagnostic", action="store_true")
    reuse = sub.add_parser("prepare-reuse")
    reuse.add_argument("--output", required=True)
    reuse.add_argument("--model", required=True)
    reuse.add_argument("--repeats", type=int, default=3)
    reuse.add_argument("--seed", type=int, default=42)
    reuse.add_argument("--context-budget", type=int, default=2400)
    reuse.add_argument("--capture-trial")
    for preparation in (capture, reuse):
        preparation.add_argument("--embedding-model")
        preparation.add_argument("--embedding-revision")
        preparation.add_argument("--lexical-diagnostic", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("trial")
    run.add_argument("--image", required=True)
    run.add_argument("--timeout", type=int, default=600)
    run.add_argument("--network", choices=("none", "bridge"), default="none")
    run.add_argument("--env-file")
    run.add_argument("--grade", action="store_true")
    score = sub.add_parser("score-capture")
    score.add_argument("trial")
    score.add_argument("--scorecard")
    summary = sub.add_parser("summarize-reuse")
    summary.add_argument("directory")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-capture":
            result = prepare_capture(args.output, args.model, args.embedding_model,
                                     args.embedding_revision, args.lexical_diagnostic)
        elif args.command == "retrieval":
            result = semantic_eval(args.output, args.model, args.revision, args.k, args.threshold, args.lexical_diagnostic)
        elif args.command == "prepare-reuse":
            result = prepare_reuse(args.output, args.model, args.repeats, args.seed, args.context_budget, args.capture_trial,
                                   args.embedding_model, args.embedding_revision, args.lexical_diagnostic)
        elif args.command == "run":
            result = run_trial(args.trial, args.image, args.timeout, args.network, args.env_file, args.grade)
        elif args.command == "score-capture":
            result = score_capture(args.trial, args.scorecard)
        else:
            result = summarize_reuse(args.directory)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "score-capture":
            return 0 if result["status"] == "passed" else 1
        if args.command == "summarize-reuse":
            return 0 if all(t["status"] == "passed" for t in result["trials"]) else 1
        return 1 if result.get("passed") is False or result.get("status") in ("failed", "invalid_run") else 0
    except (KnowledgeError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
