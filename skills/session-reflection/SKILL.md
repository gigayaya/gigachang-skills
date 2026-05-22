---
name: session-reflection
description: Use when the user explicitly asks to reflect on, review, or learn from the current Claude Code session — e.g. "反省", "檢討這次 session", "review this session", "why did that take so many tries", "what went wrong this session", or asks to turn this session's mistakes into project rules. Reads the session transcript, finds where Claude's output was rejected or required correction, distills the root causes, and proposes concrete project rules — integrating them into the project's existing rule system (CLAUDE.md, AGENTS.md, …) or proposing a simple one if none exists. Manual-trigger only — never auto-invoke; never write rule files without explicit user approval.
---

# Session Reflection

When invoked, look back over the **current session** and figure out where
Claude's work was **rejected or required the user to ask for changes**, why it
wasn't right the first time, and what **project rule** would prevent the same
miss next time. Then propose those rules to the user.

The goal is durable improvement: each reflection turns this session's friction
into rules that make the next session smoother.

## When to invoke

- **Manual only.** The user explicitly asks to reflect / review / 檢討 the
  session, or to turn its mistakes into rules.
- **Never auto-invoke**, and never edit any file until the user approves.

## Workflow

### Step 1 — Extract the friction log

Run the helper script. It is standard-library Python — no install needed.

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/session-reflection/scripts/extract_friction_log.py
```

With no arguments it auto-detects the current session's transcript and writes
a compact **friction log** to a temp file, printing that path to stdout.

If it cannot locate the transcript, it exits with a message. In that case ask
the user for their session transcript path and re-run with
`--transcript <path>`.

### Step 2 — Read the friction log

Read the file the script printed. It is a numbered timeline of user prompts,
tool calls, and results, with friction points flagged:

- `<<REJECTED>>` — a tool call the user refused.
- `<<ERROR>>` — a tool call or command that failed.

### Step 3 — Analyze the friction

Identify each **episode** where Claude's output was rejected, errored, or the
user had to ask for a correction or redo. The script flags rejections and
errors mechanically; **user corrections are a judgment call** — read the
wording of user prompts that follow Claude's work (e.g. "不對，改成…", "no, do
it differently", a re-prompt repeating the request) and decide.

Ignore the final user prompt that triggered this reflection — it is not
friction.

For each episode, note:

- **What Claude did** that missed.
- **How the user pushed back** (rejected / corrected / re-ran).
- **Root cause** — pick the real one: missing context, wrong assumption,
  skipped a step, violated a project convention, over-engineered, didn't
  verify before claiming done, etc.

Group repeated root causes into patterns — a pattern that recurs is the
strongest rule candidate.

### Step 4 — Derive candidate rules

For each root cause (or pattern), write one **concrete, actionable rule** that
would have prevented the miss. Each rule:

- **Directive** — an imperative sentence ("Always …", "Before …, …", "Never …").
- **Why** — one line of rationale tied to what went wrong this session.
- **Example** — optional, only when it sharpens the rule.

Rules must be specific and verifiable. Reject vague platitudes ("write better
code", "be more careful") — they teach nothing.

### Step 5 — Detect the project's rule system

Look, in this order, for an existing rule system in the project:

1. `CLAUDE.md` — repo root, then `.claude/CLAUDE.md`
2. `AGENTS.md`
3. `.cursor/rules/` or `.cursorrules`
4. `.github/copilot-instructions.md`

- **If one exists** — plan to add the new rules to it, matching its existing
  structure, heading style, and tone.
- **If none exists** — propose creating `CLAUDE.md` at the repo root as the
  project's rule system. Keep it simple: a single section (e.g.
  `## Project Rules` or `## Lessons Learned`) holding the rules in the Step 4
  format. Tell the user this file becomes the project's rule system and
  Claude Code reads it automatically each session.

### Step 6 — Propose to the user

Present, in the chat:

1. The **root-cause analysis** — the episodes and patterns you found.
2. The **candidate rules** — numbered, in final wording.
3. **Where each rule goes** — the exact file and section.

Then ask the user to approve. They may take a subset, edit wording, or
decline. **Do not edit any file before they approve.**

### Step 7 — Apply the approved rules

Only after approval:

- Edit or create **only the rule file**. Touch nothing else.
- Before writing, **de-duplicate** against rules already in that file — if a
  rule already covers it, skip or merge rather than repeat.
- Match the file's existing format.

### Step 8 — Report

Tell the user which rules were added and to which file, so they can review the
diff.

## Notes

- The analysis stays in the conversation — this skill does not save a
  separate report file. Only approved rules are persisted, into the rule file.
- The friction log is a temp file; you may leave it or delete it after use.
- The helper script reads the transcript at `~/.claude/projects/<encoded-cwd>/`.
  Detecting "user asked for a change" is semantic — the script surfaces the
  raw prompts; the judgment in Step 3 is yours.
