"""Container entry point for an explicitly configured coding-agent command.

EVAL_AGENT_COMMAND_JSON is an argv array containing one {prompt} placeholder.
No shell is used. Configure the command to start a NEW session and emit raw tool
traces. Install that agent in your own image derived from evaluation/Dockerfile.
"""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text())
    command = json.loads(os.environ.get("EVAL_AGENT_COMMAND_JSON", "[]"))
    if not isinstance(command, list) or not command or not all(isinstance(v, str) for v in command):
        raise SystemExit("Set EVAL_AGENT_COMMAND_JSON to a fresh-session coding-agent argv array.")
    if sum(v.count("{prompt}") for v in command) != 1:
        raise SystemExit("Agent argv must contain exactly one {prompt} placeholder.")
    model = os.environ.get("EVAL_MODEL_ID")
    if request.get("model") and model != request["model"]:
        raise SystemExit("EVAL_MODEL_ID must match the predeclared experiment model/version.")
    prompt = "Perform this evaluation task using the available files and tools.\n" + json.dumps(request, indent=2)
    argv = [arg.replace("{prompt}", prompt) for arg in command]
    Path("/tmp/agent-home").mkdir(exist_ok=True)
    auth = Path("/run/codex-auth.json")
    if auth.exists():
        private_home = Path("/tmp/agent-home/.codex")
        private_home.mkdir(mode=0o700, exist_ok=True)
        shutil.copyfile(auth, private_home / "auth.json")
        (private_home / "auth.json").chmod(0o600)
    # Bind mounts can retain the host owner's UID. Trust only the two fixture
    # repositories, and only in this container process tree.
    agent_env = {**os.environ, "HOME": "/tmp/agent-home", "GIT_CONFIG_COUNT": "2",
                 "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": "/workspace/project",
                 "GIT_CONFIG_KEY_1": "safe.directory", "GIT_CONFIG_VALUE_1": "/workspace/knowledge"}
    started = time.monotonic()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep raw output as evidence; never parse a claimed 'success' as a score.
    with (output.parent / "agent-trace.txt").open("w") as stdout, (output.parent / "agent-errors.txt").open("w") as stderr:
        process = subprocess.run(argv, cwd=request["project"], stdout=stdout, stderr=stderr, env=agent_env)
    result = {"model": model, "agent_exit_code": process.returncode, "wall_seconds": time.monotonic() - started,
              "tokens_input": None, "tokens_output": None, "tool_calls": None, "human_corrections": None,
              "trace": "agent-trace.txt", "metrics_source": "unavailable; inspect native trace independently"}
    if request.get("cli"):
        refs = subprocess.run(["git", "-C", "/workspace/knowledge", "for-each-ref", "--format=%(refname:short)",
                               "refs/heads/knowledge/"], capture_output=True, text=True, check=True, env=agent_env).stdout.splitlines()
        if len(refs) > 1:
            raise SystemExit("Multiple proposal branches; inspect the trace rather than choosing one silently.")
        result.update(outcome="proposal" if refs else "zero_qualifying_candidates", proposal_branch=refs[0] if refs else None)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
