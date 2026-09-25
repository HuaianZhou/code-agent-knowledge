# Task-end capture through standing project instructions

Codex loads project `AGENTS.md` guidance at session start, and skills can be invoked
explicitly or selected implicitly. See the official
[AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and
[skills guide](https://learn.chatgpt.com/docs/build-skills).

For this tool, use a standing completion policy when you want capture considered
without repeating it in every coding request. This remains model-followed guidance,
not a guaranteed post-completion callback. Crashes, interruptions, conflicting
instructions, unavailable tools or missed instructions can prevent completion.

## Configure a project

After installing the CLI and creating or cloning the nodes repository, take the
[policy fragment](../integrations/codex/AGENTS.fragment.md), replace its three
placeholders, and append it to the coding project's existing `AGENTS.md` without
discarding its existing instructions:

- `SKILL_PATH`: absolute path to this tool's `skills/knowledge-extract/SKILL.md`.
- `CLI_COMMAND`: the installed CLI invocation with `--config` pointing to this
  project's knowledge-store configuration. Quote executable/config paths containing
  spaces according to the agent's shell.
- `REPOSITORIES_PATH`: JSON mapping logical repository names to local code paths.

Start a fresh Codex session after configuring the policy. Skill and config paths
must exist in that agent's execution environment; container paths differ from
Windows host paths. The CLI install script does not install this policy globally.
Removing the added section opts the project out. An explicit user request to skip
capture takes precedence.

The policy runs the existing admission and search workflow, permits zero writes,
and authorizes local proposals only. Review/acceptance remains separate. It does
not direct the agent to record every conversation or every completed task.

## Test without a task-specific reminder

`python -m evaluation.task_end_trigger OUTPUT` prepares two fresh stores and coding
projects, with identical standing policies and no capture instructions, skill path,
or CLI pointer in either task request:

1. A streaming refactor with the F-17/F-18 operational handoff: expect an actionable
   reported receiver constraint to be proposed, without prescribing a node count.
2. A code-only inventory fix: expect the workflow to run but submit zero knowledge.

Use `evaluation.fulfillment_run` to execute both through the existing isolated Astra
runtime. Inspect native commands for skill reading and successful `task-end` or
`propose`; separately inspect Git artifacts, evidence quality and zero-write status.
The coding grader alone cannot establish that capture happened. A node count alone
cannot establish that the skill was correctly executed. Do not count the agent's
final claim as the only evidence.

This evaluates standing-policy compliance, not discovery from a skill description
alone, not a host hook, and not unattended recovery after interruption.

## Observed pilot results

The [2026-09-25 workflow report](results/agent-workflows-20260925.md) records
completed Astra runs, native evidence, independent grades and limitations.
