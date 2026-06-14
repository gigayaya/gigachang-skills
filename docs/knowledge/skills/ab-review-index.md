# ab-review

Dispatches two opposing sub-agents (pro/con) to review a diff in parallel; the main agent verifies each side's cited evidence against the repo, then reads both reports and judges. Sub-agents live in repo-root `agents/`, so this folder only holds skill docs.

| Path | What it is | When to read |
|---|---|---|
| `skills/ab-review/SKILL.md` | Frontmatter + workflow: when to trigger, scope selection, dual-agent dispatch protocol, evidence-verification step, main-agent judging rules | Adjusting trigger conditions or dispatch flow |
| `skills/ab-review/scripts/verify_evidence.py` | Stdlib-only verifier: greps each reviewer's JSON evidence snippets against the repo, flags unverified (esp. strong) citations | Changing how citations are validated |
| `skills/ab-review/README.md` | User-facing docs for the skill | Changing user-visible behaviour or usage |
| `commands/ab-review.md` | Slash command `/ab-review` that invokes this skill | Renaming the command, editing its `description` / `argument-hint` / invocation prompt |
| `agents/ab-review-pro.md` | PRO sub-agent definition: argues the change is correct and should merge | Editing the PRO stance, allowed tools, or its evidence rules |
| `agents/ab-review-con.md` | CON sub-agent definition: argues the change is flawed and must not merge | Editing the CON stance, allowed tools, or its evidence rules |
