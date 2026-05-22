# session-reflection

Look back over the current Claude Code session, find where Claude's output was
**rejected or required the user to ask for changes**, distill *why* it wasn't
right the first time, and propose concrete **project rules** so the same
mistake doesn't happen next session.

Triggered manually when you ask Claude to reflect on the session. It
never auto-runs and never writes rule files without your approval.

## How Claude uses it

1. Claude runs `extract_friction_log.py`, which locates the current session's
   transcript and distills it into a compact **friction log** — a numbered
   timeline with every rejected (`<<REJECTED>>`) and errored (`<<ERROR>>`)
   tool call flagged.
2. Claude reads that log, identifies each friction episode, and works out the
   root cause — missing context, wrong assumption, skipped step, violated
   convention, and so on.
3. Claude turns the root causes into candidate rules and detects the project's
   rule system (`CLAUDE.md`, `AGENTS.md`, …), or proposes creating `CLAUDE.md`
   if none exists.
4. Claude presents the analysis and proposed rules and asks you to approve.
   Only approved rules get written, only to the rule file.

The split is the same as the sibling skill: the **script does the
transformation** (large noisy JSONL → compact friction log), the **LLM does
the understanding** (root-cause analysis, rule writing). The script stays
small and testable; the contract between them is the friction-log markdown.

## Required dependencies

**None.** `extract_friction_log.py` uses only the Python 3 standard library —
no `pip install` step.

## File layout

```
session-reflection/
├── SKILL.md                       # skill description + workflow
├── README.md                      # this file
└── scripts/
    └── extract_friction_log.py    # transcript JSONL → friction log
```

## Standalone CLI usage

The extractor works without Claude — useful for testing:

```bash
# auto-detect the current session by matching cwd + newest mtime
python scripts/extract_friction_log.py

# or point at a specific transcript
python scripts/extract_friction_log.py \
  --transcript ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl \
  --out friction-log.md
```

It prints the absolute path of the friction log on stdout.

## How the transcript is found

Claude Code stores each session as a JSONL transcript under
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. With no `--transcript`,
the script scans those files, keeps the ones whose recorded `cwd` matches the
current directory, and picks the **most-recently-modified** match — the live
session is always the newest, so this resolves to the current session.

## Limits

- Reads transcripts from the default `~/.claude/projects/` location. A
  non-standard `CLAUDE_CONFIG_DIR` is not auto-detected — pass `--transcript`.
- **Hard rejections and errors** are detected mechanically. "The user asked
  for a change" is semantic — the script surfaces the raw prompts and Claude
  judges which were corrections.
- Reflects on **one session at a time**; it does not aggregate across sessions.
- Long messages and tool results are truncated in the friction log to keep it
  compact; rejections and errors are kept at greater length.
