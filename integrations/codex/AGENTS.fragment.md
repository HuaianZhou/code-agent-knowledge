## Task-end knowledge capture

Before your final response after completing a coding task, run the knowledge-extract
workflow at `{{SKILL_PATH}}` using the current conversation and inspected evidence.
Use this CLI consistently: `{{CLI_COMMAND}}`.
Repository identities and paths are in `{{REPOSITORIES_PATH}}`; inspect applicable
project skills before deciding that a claim is not already covered.

Search existing knowledge before creating or updating a node. Preserve source,
scope and uncertainty. Do not capture credentials, personal data, generic advice,
or facts cheaply recoverable from code. Zero qualifying candidates is valid:
execute the workflow's empty-manifest submission and report no knowledge changes.

This standing policy authorizes local proposals only. Leave nonempty proposals for
separate review; do not self-accept, push, or publish them. Report the actual proposal
or zero-write result briefly with the coding outcome. If capture is blocked, report
the blocker accurately without claiming it ran. Honor an explicit user instruction
to skip capture. Do not recursively capture the act of capturing knowledge.
