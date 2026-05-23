# ab-review

Dispatches two opposing sub-agents (pro/con) to review a diff in parallel; the main agent reads both reports and judges. Sub-agents live in repo-root `agents/`, so this folder only holds skill docs.

| Path | What it is | When to read |
|---|---|---|
| `skills/ab-review/SKILL.md` | Frontmatter + workflow: when to trigger, scope selection, dual-agent dispatch protocol, main-agent judging rules | Adjusting trigger conditions or dispatch flow |
| `skills/ab-review/README.md` | User-facing docs for the skill | Changing user-visible behaviour or usage |
| `commands/ab-review.md` | Slash command `/ab-review` that invokes this skill | Renaming the command, editing its `description` / `argument-hint` / invocation prompt |
| `agents/ab-review-pro.md` | PRO sub-agent definition: argues the change is correct and should merge | Editing the PRO stance, allowed tools, or its evidence rules |
| `agents/ab-review-con.md` | CON sub-agent definition: argues the change is flawed and must not merge | Editing the CON stance, allowed tools, or its evidence rules |
