# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project rules

- **English only.** All content in this repository — code, comments,
  documentation, skill `description` fields, examples, and commit messages —
  must be written in English. No Chinese or other non-English text in project
  files.

## What this is

`gigachang-skills` is a Claude Code **plugin** that bundles personal-workflow
skills. It is not an application: there is no build step, server, or test
framework. "Running" the project means running a skill's standalone script, or
having Claude Code invoke a skill.

## Architecture

Every skill follows a deliberate **"LLM understands / script transforms"
split** — understanding this is the key to working in either skill:

- The **LLM** reads `SKILL.md`, does the judgment/understanding work, and
  produces **structured intermediate data**.
- A **standalone Python script** does the deterministic **transformation**.
- A **documented data format is the contract** between the two. This keeps the
  scripts small, unit-testable, and runnable as plain CLIs without Claude.

The two skills instantiate that pattern:

- `markdown-to-html-report` — Claude produces a `metadata.json` (full schema in
  its `SKILL.md`); `scripts/render_report.py` renders the source markdown +
  that metadata into one self-contained HTML file. `vendor/` assets
  (highlight.js, mermaid.js) are smart-inlined at render time.
- `session-reflection` — `scripts/extract_friction_log.py` distills a Claude
  Code session transcript (`~/.claude/projects/<encoded-cwd>/*.jsonl`) into a
  compact friction log; Claude then analyzes it and proposes project rules.

A skill is a directory `skills/<name>/` holding `SKILL.md` (YAML frontmatter
with `name` + `description`) plus `README.md` and supporting assets. The
frontmatter **`description` is what triggers the skill** — it must describe
when to invoke and when to skip. Claude Code auto-discovers skills at session
start; there is no registration. Skills reference their own bundled files via
the `${CLAUDE_PLUGIN_ROOT}` env var so paths survive installation.

Distribution: `.claude-plugin/plugin.json` is the manifest and holds the
version; `.claude-plugin/marketplace.json` makes the repo installable as its
own single-plugin marketplace.

## Commands

No build, lint, or automated test tooling exists. Scripts are verified by
running them standalone (each skill's `README.md` documents standalone CLI
usage).

`markdown-to-html-report` — requires Python 3.9+ and four packages:

```bash
pip install -r skills/markdown-to-html-report/scripts/requirements.txt
python skills/markdown-to-html-report/scripts/render_report.py <markdown> <metadata.json> <output.html>
```

`session-reflection` — Python standard library only, no install:

```bash
python skills/session-reflection/scripts/extract_friction_log.py [--transcript PATH] [--out PATH]
```
