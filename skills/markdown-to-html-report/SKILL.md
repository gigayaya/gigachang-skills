---
name: markdown-to-html-report
description: Use when about to present long or complex AI-generated markdown to the user — typically >150 lines, >5 H2 sections, or content like code reviews, implementation plans, specs, research reports. Also use when the user explicitly asks to convert a markdown source into a readable HTML report. Produces a single self-contained HTML report (TL;DR hero, sticky TOC with importance stars, semantic-color callouts, syntax-highlighted code, mermaid diagrams, inline concept explanations, dark mode, magazine reading layout) saved to ./claude-reports/. Skip for short, simple, or plain-text content where the conversion cost outweighs the reader's time savings.
---

# Markdown to HTML Report

Turn long AI-generated markdown into a human-friendly self-contained HTML report — designed to minimize reader cognitive load via TL;DR, collapsible sections, semantic colors, and inline concept explanations.

**This skill rewrites, it does not photocopy.** The source markdown is raw material, not the final body. Each section is re-authored into flowing prose that reads like a well-edited tech article — not a bullet dump. The work splits in three: the `markdown-report-analyst` sub-agent does the *understanding and editing* (it reads the source and produces the rewritten `metadata.json`), the renderer does the deterministic HTML *transformation*, and this skill *orchestrates* the two. Copy-pasting the source verbatim into the report is the single most common failure mode and is explicitly wrong.

## When to invoke

**Auto-trigger heuristic** (use judgment, not strict thresholds):
- Output is ≥150 lines OR has ≥5 H2/H3 sections
- Content type is: code review, implementation plan, design spec, research report, audit, or similar long-form analysis
- The reader (user) clearly benefits from skim-then-deep-read flow

**Manual trigger:** user explicitly asks ("convert this to HTML report", "make a readable version", or hands you a markdown file/string).

**Skip when:**
- Content is short (<~80 lines)
- Content is conversational, a single answer, or plain-text-suitable
- User is mid-flow and doesn't want a side artifact

## Workflow

### Step 1 — Resolve the markdown source

The source can be:
- **A file path** the user provided → read it directly
- **A pasted markdown string** → write to `./claude-reports/.tmp-input.md`
- **Markdown you just produced** in this conversation → write to `./claude-reports/.tmp-input.md`

Note the `markdown_dir` (parent of the markdown file) — it's used to resolve relative image paths.

### Step 2 — Dispatch the analyst sub-agent (understand + rewrite + metadata)

The comprehension-heavy half — reading the source, understanding it, re-authoring each section into distilled prose, and producing `metadata.json` — is delegated to the bundled `markdown-report-analyst` sub-agent. You do **not** read and rewrite the article yourself.

In a single `Agent` call, dispatch `subagent_type: markdown-report-analyst` and pass it:

- the **markdown source path** from Step 1,
- the **`markdown_dir`** (parent of the source, for resolving relative image paths),
- the **metadata output path** it must write: `./claude-reports/.tmp-report.json`.

The agent already carries the full contract — the metadata schema, the body-rewriting rules, the hero-SVG rules, the glossary/diagram rules, the same-language rule, and the no-fabrication rule — defined in `agents/markdown-report-analyst.md`. **Do not re-specify any of that here, and do not do the rewriting yourself.**

When it returns, it reports the metadata path it wrote, the `slug` it chose, the section count, estimated read minutes, and the must-read/diagram counts. Use the metadata path and slug in Steps 3–4, and the counts in your Step 5 message.

### Step 3 — Verify fidelity (mandatory)

The analyst is a rewriter, so its output must be checked, not trusted. Run
the verifier (standard-library Python, no install needed):

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/verify_fidelity.py \
  <markdown_path> ./claude-reports/.tmp-report.json --json
```

It compares the metadata against the source. **Errors** (exit 1): a source
H2/H3 section that no section covers, merges, or declares omitted; a
fabricated section heading; a source code block missing or altered in the
rewritten bodies; a `must_read_quote` not verbatim in its section body.
**Warnings** (exit 0): declared omissions (with the analyst's reason), source
fact tokens (numbers, inline code, paths, URLs) missing from the rewritten
report, language drift.

Handle the result:

1. **No errors** → proceed to Step 4. Use judgment on warnings; mention
   notable ones (declared omissions, lost fact tokens) in your Step 5
   message.
2. **Errors** → send the full JSON report back to the **same** analyst agent
   via `SendMessage`, asking it to repair the metadata file in place (its
   agent file defines the repair protocol). Re-run the verifier. At most
   **2** repair rounds.
3. **Still failing after 2 rounds** → show the user the unresolved errors and
   ask whether to render anyway (with the issues noted) or abort. Never
   silently render a report that failed verification.

### Step 4 — Run the renderer

First-time setup (one-shot per machine):
```bash
pip install -r ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/requirements.txt
```

If `pip install` fails or dependencies are missing, ask the user to run the install command themselves before proceeding.

Then render, using the metadata path the analyst wrote and the `<slug>` it returned:
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/render_report.py \
  <markdown_path> \
  ./claude-reports/.tmp-report.json \
  ./claude-reports/$(date +%Y%m%d-%H%M%S)-<slug>.html
```

**If the markdown source is a temp file** (a pasted string or markdown you
produced in chat, written to `./claude-reports/.tmp-input.md`), the source's
folder is no longer where its relative images live. Pass the original
`markdown_dir` from Step 1 so relative images still resolve:
```bash
  ... --image-base <markdown_dir>
```
When the source is a real file the user gave, omit the flag — it defaults to
the file's own folder.

The script prints the absolute output path on stdout. The metadata contract is unchanged — the renderer behaves identically whether the metadata was authored inline or by the sub-agent.

### Step 5 — Cleanup and report

- Delete the `.tmp-*.md` and `.tmp-*.json` files
- If `./claude-reports/` was just created, remind the user once: *"I created `./claude-reports/` for HTML reports — consider adding it to .gitignore."*
- Tell the user the report is ready and provide the `file://<absolute-path>` link they can cmd-click to open

Example final message:
> Report ready: `file:///Users/you/proj/claude-reports/20260510-143022-pr-review.html` (12 min read, 8 sections, 3 must-read highlights). Reads top-to-bottom like a tech blog — use the **Skim** button in the top bar to collapse sections for index-style overview.

## Notes

- **The analyst sub-agent owns Step 2.** Reading, understanding, and rewriting the article — plus authoring `metadata.json` — all live in `agents/markdown-report-analyst.md`. This skill orchestrates (resolve source → dispatch agent → verify → render → report); it does not rewrite the article inline. If you need to change *how* the article is understood or rewritten (rewrite intensity, schema, SVG/glossary rules), edit the agent file, not this one.
- The output is fully self-contained: opens offline, all CSS / JS / hero SVG inlined. Exception: image URLs (http/https) inside the markdown body remain as links and need network to display.
- mermaid.js (~3 MB) is only inlined when the report actually contains diagrams — keep `auto_diagrams` empty if the content doesn't need diagrams.
- highlight.js is only inlined when there's at least one code block.
- **Sections default to expanded.** The report reads like a tech blog top-to-bottom. The top bar's **Skim** button collapses every section to heading + lead-in; clicking a heading in skim mode opens just that section.
- **Hero SVG is sanitized** by a separate whitelist — `<script>`, event handlers, `style="…"` attrs, and unrecognized tags are stripped. Keep the SVG self-contained (no external `href`).
- **Glossary tooltips are pure CSS hover** (with keyboard focus support). They appear over body text; the bottom Glossary section is still rendered as a quick index.
- HTML body is sanitized via a whitelist (allows `<mark>`, `<kbd>`, `<details>`, etc.; strips `<script>`, `<iframe>`, event handlers).
