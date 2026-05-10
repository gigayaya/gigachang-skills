# markdown-to-html-report

Turn long AI-generated markdown into a single self-contained HTML report optimized for human reading — TL;DR hero, sticky TOC with importance stars, semantic-color callouts, syntax-highlighted code, mermaid diagrams, inline concept explanations, dark mode, and a magazine reading layout.

Designed to be triggered automatically when Claude is about to dump a long markdown artifact (code review, implementation plan, spec, research report) on the user, or invoked manually with a markdown source.

## Output

A single `.html` file written to `./claude-reports/<timestamp>-<slug>.html` in the user's current working directory. The file is fully self-contained: all CSS / JS is inlined, so you can move it, archive it, or attach it to a ticket without breaking it. Image URLs (`http(s)://`) remain as links and need network to display; local image paths are inlined as base64.

## Required dependencies

This skill ships a Python script that does the markdown → HTML conversion. You need Python 3.9+ and the four packages below.

### One-time install

```bash
pip install -r ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/requirements.txt
```

Or, with absolute path (substitute your plugin install location):

```bash
pip install -r <plugin-root>/skills/markdown-to-html-report/scripts/requirements.txt
```

### Packages

| Package | Purpose |
|---|---|
| `markdown` (≥3.6) | Markdown → HTML conversion with extras (tables, fenced code, attr_list, def_list, admonition, toc) |
| `pygments` (≥2.18) | Server-side syntax highlighting for code blocks |
| `jinja2` (≥3.1) | HTML template rendering |
| `bleach` (≥6.1) | HTML whitelist sanitization (strips `<script>`, `<iframe>`, `on*` event handlers, `javascript:` URLs) |

If `pip install` fails, ask the user to run it themselves. The script will raise a clear `ModuleNotFoundError` if a dep is missing.

### Optional: isolated environment

If you don't want to pollute your system Python:

```bash
# with uv
uvx --with markdown,pygments,jinja2,bleach python <script-path> ...

# or a venv
python3 -m venv ~/.venvs/md-report
source ~/.venvs/md-report/bin/activate
pip install -r .../requirements.txt
```

## How Claude uses it

1. Claude reads the source markdown and produces a `metadata.json` (TL;DR, per-section overviews, must-read quotes, callouts, concept explanations, optional auto-generated mermaid diagrams, next actions). Schema is documented in [`SKILL.md`](./SKILL.md).
2. The renderer script reads both files and emits a self-contained HTML.
3. Claude reports the `file://` path back to the user.

The split is deliberate: LLM does the *understanding*, the script does the *transformation*. Adds a clean contract between the two and keeps the script unit-testable.

## File layout

```
markdown-to-html-report/
├── SKILL.md                  # Skill description + metadata schema + workflow
├── README.md                 # this file
├── scripts/
│   ├── render_report.py      # main converter; CLI: <md> <metadata.json> <out.html>
│   └── requirements.txt      # Python deps
├── templates/
│   └── report.html.j2        # Jinja2 template (page shell + interactivity JS)
├── styles/
│   └── magazine.css          # serif/sans hybrid, warm accent, dark mode
└── vendor/                   # smart-inlined into HTML at render time
    ├── highlight.min.js
    ├── highlight-github.min.css
    ├── highlight-github-dark.min.css
    └── mermaid.min.js        # ~3 MB; only inlined when the report has diagrams
```

## Standalone CLI usage

The renderer also works as a plain CLI without Claude — useful for testing template changes:

```bash
python scripts/render_report.py <markdown_path> <metadata.json> <output.html>
```

It prints the absolute output path on stdout.

## Customizing

- **Visual tweaks** — edit `styles/magazine.css`. CSS variables at the top control colors, fonts, spacing.
- **Template structure** — edit `templates/report.html.j2`. Inline JS at the bottom handles theme toggle, expand/collapse, code copy, scroll progress.
- **Trigger sensitivity** — edit the `description` field in [`SKILL.md`](./SKILL.md) frontmatter. Loosen or tighten the trigger heuristics there.

## Limits

- Output size is dominated by `mermaid.min.js` (~3 MB) when the report contains diagrams. For diagram-free reports the file is a few hundred KB.
- The script slices the markdown by *exact heading text match*. If two H2s share the same heading, append a discriminator (e.g., `... (cont.)`) to disambiguate.
- Sanitization is whitelist-based — if you author a markdown that intentionally embeds raw HTML, only the tags listed in `render_report.py:ALLOWED_TAGS` survive.
