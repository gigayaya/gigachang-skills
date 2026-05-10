# daily-skill-plugin

A personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) skills for daily workflows. Each skill is a small, focused capability that Claude can invoke automatically (via skill description matching) or that you can trigger manually.

## Skills in this plugin

| Skill | What it does |
|---|---|
| [markdown-to-html-report](./skills/markdown-to-html-report/) | Converts long AI-generated markdown (code reviews, plans, specs) into a single self-contained HTML report — TL;DR, sticky TOC, semantic callouts, syntax highlighting, mermaid diagrams, dark mode |

---

## Installation

### 1. Install the plugin in Claude Code

This plugin is published as its own single-plugin marketplace at [`gigayaya/daily-skill-plugin`](https://github.com/gigayaya/daily-skill-plugin). Install in two steps inside any Claude Code session:

```text
/plugin marketplace add gigayaya/daily-skill-plugin
/plugin install daily-skill-plugin@daily-skill-plugin
```

(Yes, the name is repeated — `<plugin-name>@<marketplace-name>`, both happen to be `daily-skill-plugin`.)

After install, `${CLAUDE_PLUGIN_ROOT}` resolves to the cached plugin directory. Every skill in this repo uses that variable so paths stay portable.

#### Updating

```text
/plugin marketplace update daily-skill-plugin
/plugin update daily-skill-plugin@daily-skill-plugin
```

You can also enable auto-update under `/plugin` → **Marketplaces**.

### 2. Install per-skill dependencies

Some skills ship runtime scripts that need third-party libraries. Install them once per machine.

#### markdown-to-html-report — Python deps

Requires Python 3.9+ and four packages (`markdown`, `pygments`, `jinja2`, `bleach`):

```bash
pip install -r ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/requirements.txt
```

For full setup options (uv, venv, troubleshooting), see [`skills/markdown-to-html-report/README.md`](./skills/markdown-to-html-report/README.md#required-dependencies).

---

## Verifying the install

Open a Claude Code session and ask:

> List the skills you have available.

`markdown-to-html-report` should appear in the list. To smoke-test it end-to-end, ask Claude to:

> Convert this README into an HTML report.

You should see Claude invoke the skill, run the renderer, and hand you back a `file://` link to a `.html` file in `./claude-reports/`.

---

## Repository layout

```
daily-skill-plugin/
├── .claude-plugin/
│   ├── plugin.json                # plugin manifest (name, version, author, ...)
│   └── marketplace.json           # single-plugin marketplace entry (for /plugin install)
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md               # frontmatter (name + description) + workflow
│       ├── README.md              # human-facing docs + dependency setup
│       └── ...                    # scripts, templates, assets per skill
├── LICENSE
└── README.md                      # this file
```

Add a new skill by creating `skills/<your-skill>/SKILL.md` with a `name` and `description` in YAML frontmatter — Claude Code auto-discovers it on next session start.

---

## License

MIT — see [LICENSE](./LICENSE).
