# Codemap

## General files

| Path | What it is | When to read |
|---|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest, holds the `version` | Bumping version after any functional change |
| `.claude-plugin/marketplace.json` | Single-plugin marketplace entry | Changing how the plugin is installable |
| `README.md` | User-facing overview + canonical Repository layout tree | Reference when uncertain about the full file tree |

## Skill indexes

| Skill | Index | What it does |
|---|---|---|
| `ab-review` | [skills/ab-review-index.md](skills/ab-review-index.md) | Dual-agent pro/con review of a diff, judged by the main agent |
| `markdown-to-html-report` | [skills/markdown-to-html-report-index.md](skills/markdown-to-html-report-index.md) | Long markdown → self-contained magazine-style HTML report |
| `scope-research` | [skills/scope-research-index.md](skills/scope-research-index.md) | Surveys the codebase for a proposed change, reports per-touchpoint facts |
| `session-reflection` | [skills/session-reflection-index.md](skills/session-reflection-index.md) | Extracts session friction and proposes project rules to prevent it |
