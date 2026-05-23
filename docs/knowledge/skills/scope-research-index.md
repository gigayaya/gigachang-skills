# scope-research

Surveys the codebase for a proposed change and reports concrete facts about each touchpoint (no t-shirt sizes, no verdicts). The surveyor sub-agent lives in repo-root `agents/`.

| Path | What it is | When to read |
|---|---|---|
| `skills/scope-research/SKILL.md` | Frontmatter + workflow: requirement anchoring, convention detection, initial scan, parallel surveyor dispatch, report format | Adjusting trigger conditions, survey flow, or report format |
| `skills/scope-research/README.md` | User-facing docs for the skill | Changing user-visible behaviour |
| `commands/scope-research.md` | Slash command `/scope-research` that invokes this skill | Renaming the command, editing its `description` / `argument-hint` / invocation prompt |
| `agents/scope-research-surveyor.md` | Surveyor sub-agent definition: investigates one focus area and returns neutral facts | Editing the surveyor's contract, allowed tools, or fact-reporting rules |
