---
name: markdown-to-html-report
description: Use when about to present long or complex AI-generated markdown to the user — typically >150 lines, >5 H2 sections, or content like code reviews, implementation plans, specs, research reports. Also use when the user explicitly asks to convert a markdown source into a readable HTML report. Produces a single self-contained HTML report (TL;DR hero, sticky TOC with importance stars, semantic-color callouts, syntax-highlighted code, mermaid diagrams, inline concept explanations, dark mode, magazine reading layout) saved to ./claude-reports/. Skip for short, simple, or plain-text content where the conversion cost outweighs the reader's time savings.
---

# Markdown to HTML Report

Turn long AI-generated markdown into a human-friendly self-contained HTML report — designed to minimize reader cognitive load via TL;DR, collapsible sections, semantic colors, and inline concept explanations.

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

### Step 2 — Detect language and produce metadata

Read the markdown carefully. Detect its primary language (zh-TW, en, ja, …). **All LLM-produced text in metadata MUST be in the same language as the source.** Then produce a `metadata.json` matching this schema:

```jsonc
{
  "title": "string — the document's main title",
  "slug": "kebab-case-from-title (used in output filename)",
  "lang": "zh-TW | en | ...",
  "tldr": "string — 1-3 sentences capturing the entire document",
  "estimated_read_minutes": 12,

  // Hero illustration shown right under the title. REQUIRED for any report
  // long enough to warrant this skill — the report opens with a visual,
  // not a wall of text. Prefer hero_image_svg (inline, self-contained).
  "hero_image_svg": "string — inline <svg>…</svg> markup. See rules below.",
  "hero_image_path": "string (optional) — relative path to an existing png/jpg/svg next to the source markdown. If set, wins over hero_image_svg.",

  "sections": [
    {
      "id": "stable-anchor-id-from-heading",
      "heading": "exact text of the markdown heading (used to slice the markdown)",
      "level": 1-6,
      "importance": 1 | 2 | 3,
      "type": "intro | finding | action | reference | warning | note | code | idea | bug | good",
      "summary": "string — 1-2 sentence editorial lead-in shown above the section body (italic, not a card)",
      "must_read_quotes": ["VERBATIM strings copied from this section's body that the reader must not skim past"],
      "estimated_minutes": 2
    }
  ],
  "callouts": [
    { "section_id": "...", "level": "critical | warning | info | good | note", "text": "..." }
  ],
  "concepts": [
    {
      "term": "exact term as it appears in text — every occurrence in the body gets an inline hover tooltip",
      "plain_explanation": "plain-language explanation in source language (rendered as plain text inside the tooltip)",
      "analogy": "concrete analogy a fresh CS grad would understand"
    }
  ],
  "auto_diagrams": [
    {
      "after_section_id": "section_id",
      "title": "optional caption",
      "mermaid_code": "sequenceDiagram\\n  Alice->>Bob: Hi"
    }
  ],
  "next_actions": [
    "Action-oriented suggestion for the reader (e.g. 'If you're the reviewer, look at #2 and #5 first')"
  ]
}
```

**Rules for high-quality metadata:**

1. `heading` must match a real heading in the markdown EXACTLY (whitespace, punctuation, casing) — the script slices the file by heading text. If two sections share the same heading, append a discriminator like ` (cont.)` to one and update the markdown.
2. `id` must be unique, lowercase, kebab-case.
3. `must_read_quotes` must be COPIED verbatim from the body of that section. Pick 3-5 sentences max per section. Choose load-bearing claims, not boilerplate.
4. `importance`: 3 = must read; 2 = should read; 1 = optional / supplementary.
5. `type` controls the icon and a subtle accent on the heading. Pick the closest match.
6. `auto_diagrams` — only add when the section describes a sequence/flow/state machine in prose that would genuinely be clearer as a diagram. Don't generate diagrams for content that's already a list or table.
7. `concepts` — **every occurrence** of every term in the body will be wrapped in an inline hover tooltip (mouse-hover or keyboard-focus reveals it; no scrolling). Only include terms that are jargon, project-specific, or non-obvious. Don't gloss common words — over-glossing clutters the prose. The bottom-of-page Glossary list is still rendered as a printable / Ctrl-F-friendly index.
8. `hero_image_svg` — generate a tasteful inline SVG banner that visually represents the report. Rules:
   - `viewBox="0 0 1200 360"` (or similar wide aspect); width/height should be omitted or `100%`.
   - 2-4 colors total. Geometric / minimal-illustrative style. Avoid clip-art realism.
   - Embed the report title (or a short variant) as `<text>` inside the SVG.
   - **No `<script>`, no `on*` event handlers, no external `href`/`src`.** The renderer sanitizes and will strip these.
   - No `style="…"` attributes — use inline attrs (`fill="…"`, `stroke="…"`). The sanitizer drops `style`.
   - Keep it under ~3 KB. The whole thing is inlined into the HTML.
   - Minimal example (adapt — DO NOT just copy):
     ```svg
     <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360" role="img" aria-label="Report banner">
       <defs>
         <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
           <stop offset="0" stop-color="#0ea5e9"/>
           <stop offset="1" stop-color="#6366f1"/>
         </linearGradient>
       </defs>
       <rect width="1200" height="360" fill="url(#g)"/>
       <circle cx="200" cy="180" r="120" fill="#fff" fill-opacity="0.10"/>
       <text x="60" y="200" font-family="Georgia, serif" font-size="56" font-weight="700" fill="#fff">Report Title</text>
       <text x="60" y="250" font-family="sans-serif" font-size="20" fill="#fff" fill-opacity="0.85">One-line subtitle</text>
     </svg>
     ```
9. Language: if the source is Chinese, all `tldr`, `summary`, `plain_explanation`, `analogy`, `next_actions` (and any embedded SVG text) MUST be in the source language.

Write metadata to `./claude-reports/.tmp-<slug>.json`.

### Step 3 — Run the renderer

First-time setup (one-shot per machine):
```bash
pip install -r ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/requirements.txt
```

If `pip install` fails or dependencies are missing, ask the user to run the install command themselves before proceeding.

Then render:
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/markdown-to-html-report/scripts/render_report.py \
  <markdown_path> \
  ./claude-reports/.tmp-<slug>.json \
  ./claude-reports/$(date +%Y%m%d-%H%M%S)-<slug>.html
```

The script prints the absolute output path on stdout.

### Step 4 — Cleanup and report

- Delete the `.tmp-*.md` and `.tmp-*.json` files
- If `./claude-reports/` was just created, remind the user once: *"I created `./claude-reports/` for HTML reports — consider adding it to .gitignore."*
- Tell the user the report is ready and provide the `file://<absolute-path>` link they can cmd-click to open

Example final message:
> Report ready: `file:///Users/you/proj/claude-reports/20260510-143022-pr-review.html` (12 min read, 8 sections, 3 must-read highlights). Reads top-to-bottom like a tech blog — use the **Skim** button in the top bar to collapse sections for index-style overview.

## Notes

- The output is fully self-contained: opens offline, all CSS / JS / hero SVG inlined. Exception: image URLs (http/https) inside the markdown body remain as links and need network to display.
- mermaid.js (~3 MB) is only inlined when the report actually contains diagrams — keep `auto_diagrams` empty if the content doesn't need diagrams.
- highlight.js is only inlined when there's at least one code block.
- **Sections default to expanded.** The report reads like a tech blog top-to-bottom. The top bar's **Skim** button collapses every section to heading + lead-in; clicking a heading in skim mode opens just that section.
- **Hero SVG is sanitized** by a separate whitelist — `<script>`, event handlers, `style="…"` attrs, and unrecognized tags are stripped. Keep the SVG self-contained (no external `href`).
- **Glossary tooltips are pure CSS hover** (with keyboard focus support). They appear over body text; the bottom Glossary section is still rendered as a quick index.
- HTML body is sanitized via a whitelist (allows `<mark>`, `<kbd>`, `<details>`, etc.; strips `<script>`, `<iframe>`, event handlers).
