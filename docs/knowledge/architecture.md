# Architecture

Every skill follows an **"LLM understands / script transforms"** split: the
LLM reads `SKILL.md` and produces structured intermediate data; a standalone
Python script does the deterministic transformation; a documented data format
is the contract between them. This keeps scripts small, unit-testable, and
runnable as plain CLIs without Claude.

Skills are auto-discovered from `skills/<name>/SKILL.md` — the YAML
`description` field is what triggers invocation. Bundled assets are referenced
via `${CLAUDE_PLUGIN_ROOT}` so paths survive installation.
