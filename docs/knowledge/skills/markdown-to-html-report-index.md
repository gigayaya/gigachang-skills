# markdown-to-html-report

Converts long markdown into a self-contained magazine-style HTML report (TL;DR hero, sticky TOC, syntax highlighting, mermaid diagrams, dark mode). The only skill that bundles substantial assets.

| Path | What it is | When to read |
|---|---|---|
| `skills/markdown-to-html-report/SKILL.md` | Frontmatter + workflow: metadata schema, SVG rules, language handling, render command syntax | Adjusting trigger conditions, metadata spec, or language logic |
| `skills/markdown-to-html-report/README.md` | User-facing docs, standalone CLI usage, dependency setup | Changing user-visible behaviour or install steps |
| `commands/html-report.md` | Slash command `/html-report` that invokes this skill | Renaming the command, editing its `description` / `argument-hint` / invocation prompt |
| `skills/markdown-to-html-report/scripts/render_report.py` | Main renderer: reads markdown + metadata.json, emits self-contained HTML (sanitize, tooltip, SVG hero) | Changing transformation logic, fixing script bugs |
| `skills/markdown-to-html-report/scripts/requirements.txt` | Python dependencies (markdown, jinja2, bleach, …) | Bumping or adding a Python dependency |
| `skills/markdown-to-html-report/templates/report.html.j2` | Jinja2 template for the final HTML report structure | Changing overall report layout or adding sections |
| `skills/markdown-to-html-report/styles/magazine.css` | Core stylesheet: layout, dark mode, collapsible sections, semantic colour palette | Changing visual style or colour rules |
| `skills/markdown-to-html-report/vendor/highlight.min.js` | highlight.js library (inlined only when code blocks present) | Upgrading the syntax-highlight library |
| `skills/markdown-to-html-report/vendor/highlight-github.min.css` | Light-mode code highlight theme | Swapping the light-mode theme or upgrading |
| `skills/markdown-to-html-report/vendor/highlight-github-dark.min.css` | Dark-mode code highlight theme | Swapping the dark-mode theme or upgrading |
| `skills/markdown-to-html-report/vendor/mermaid.min.js` | mermaid.js library (inlined only when `auto_diagrams` present) | Upgrading the mermaid library |
