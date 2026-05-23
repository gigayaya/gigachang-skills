# session-reflection

Analyses the current session transcript, finds where Claude was rejected or had to correct itself, and proposes project rules to prevent the same friction next time.

| Path | What it is | When to read |
|---|---|---|
| `skills/session-reflection/SKILL.md` | Frontmatter + workflow: friction extraction, root-cause analysis, rule derivation, approval-before-edit protocol | Adjusting trigger conditions or reflection flow |
| `skills/session-reflection/README.md` | User-facing docs for the skill | Changing user-visible behaviour |
| `skills/session-reflection/scripts/extract_friction_log.py` | Stdlib-only Python script that distills the current session jsonl into a friction log (marks `<<REJECTED>>` / `<<ERROR>>`) | Changing friction-extraction logic or marker rules |
| `commands/reflect.md` | Slash command `/reflect` that invokes this skill | Renaming the command, editing its `description` / `argument-hint` / invocation prompt |
