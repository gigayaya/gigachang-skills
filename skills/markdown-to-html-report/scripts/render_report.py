#!/usr/bin/env python3
"""Render a markdown source + LLM-produced metadata.json into a self-contained HTML report.

Usage:
    python render_report.py <markdown_path> <metadata_json_path> <output_html_path>
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import bleach
import markdown as md_lib
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown.extensions.codehilite import CodeHiliteExtension


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
STYLES_DIR = SKILL_ROOT / "styles"
VENDOR_DIR = SKILL_ROOT / "vendor"

ICONS = {
    "intro": "📖",
    "finding": "🔍",
    "action": "✅",
    "reference": "🔗",
    "warning": "⚠️",
    "note": "📝",
    "code": "💻",
    "idea": "💡",
    "bug": "🐛",
    "good": "✨",
}

CALLOUT_ICONS = {
    "critical": "🔴",
    "warning": "🟠",
    "info": "🔵",
    "good": "🟢",
    "note": "⚪",
}

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "button", "code", "del", "div", "em",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "kbd", "li", "mark",
    "ol", "p", "pre", "s", "small", "span", "strong", "sub", "sup", "table",
    "tbody", "td", "th", "thead", "tr", "u", "ul", "details", "summary",
    "figure", "figcaption",
]

ALLOWED_ATTRS = {
    "*": ["class", "id", "title", "role", "tabindex", "aria-label"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "td": ["colspan", "rowspan", "align"],
    "th": ["colspan", "rowspan", "align", "scope"],
    "details": ["open"],
    # The copy/expand buttons we inject around code blocks are controlled markup,
    # not user content. Whitelist <button> (no event-handler attrs) so sanitize()
    # doesn't strip them; their click handlers are bound by the template's JS.
    "button": ["type"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "data"]

# Separate whitelist for hero SVG sanitization. Keeps the LLM-supplied SVG
# safe: no <script>, no event handlers, no <use href=external>.
SVG_ALLOWED_TAGS = [
    "svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline",
    "polygon", "text", "tspan", "defs", "linearGradient", "radialGradient",
    "stop", "title", "desc", "clipPath", "mask",
]

SVG_ALLOWED_ATTRS = {
    "*": [
        "id", "class", "transform", "opacity",
        "fill", "fill-opacity", "fill-rule",
        "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
        "stroke-dasharray", "stroke-opacity",
    ],
    "svg": ["xmlns", "viewBox", "width", "height", "preserveAspectRatio", "aria-label", "role"],
    "path": ["d"],
    "rect": ["x", "y", "width", "height", "rx", "ry"],
    "circle": ["cx", "cy", "r"],
    "ellipse": ["cx", "cy", "rx", "ry"],
    "line": ["x1", "y1", "x2", "y2"],
    "polyline": ["points"],
    "polygon": ["points"],
    "text": ["x", "y", "dx", "dy", "text-anchor", "font-family", "font-size", "font-weight", "font-style", "letter-spacing"],
    "tspan": ["x", "y", "dx", "dy", "text-anchor", "font-weight"],
    "linearGradient": ["x1", "y1", "x2", "y2", "gradientUnits", "gradientTransform"],
    "radialGradient": ["cx", "cy", "r", "fx", "fy", "gradientUnits", "gradientTransform"],
    "stop": ["offset", "stop-color", "stop-opacity"],
    "clipPath": ["clipPathUnits"],
    "mask": ["maskUnits", "x", "y", "width", "height"],
}

SVG_ALLOWED_PROTOCOLS = ["http", "https", "data"]


def read_metadata(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("title", "Untitled")
    data.setdefault("slug", "report")
    data.setdefault("lang", "en")
    data.setdefault("tldr", "")
    data.setdefault("estimated_read_minutes", 0)
    data.setdefault("sections", [])
    data.setdefault("callouts", [])
    data.setdefault("concepts", [])
    data.setdefault("auto_diagrams", [])
    data.setdefault("next_actions", [])
    data.setdefault("hero_image_svg", "")
    data.setdefault("hero_image_path", "")
    for s in data["sections"]:
        s.setdefault("level", 2)
        s.setdefault("importance", 1)
        s.setdefault("type", "note")
        s.setdefault("summary", "")
        s.setdefault("must_read_quotes", [])
        s.setdefault("estimated_minutes", 1)
        # Refined prose body authored by the LLM. When present it REPLACES the
        # verbatim slice of the source markdown for this section. Empty string
        # falls back to slicing the original markdown by heading (legacy behavior).
        s.setdefault("body_markdown", "")
    return data


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def split_markdown_by_sections(markdown_text: str, sections: list[dict]) -> list[tuple[dict, str]]:
    """Slice the markdown into chunks, one per metadata section.

    Strategy: find the position of each section's heading line (first match by exact
    heading text). Chunks span from one heading to the next.
    Sections without a found heading get an empty chunk.
    Any markdown content before the first matched heading becomes a synthetic preamble
    attached to nothing (skipped in section output but available later if needed).
    """
    positions: list[tuple[int, dict]] = []
    cursor = 0
    for s in sections:
        heading = s["heading"].strip()
        # search from cursor forward
        sub = markdown_text[cursor:]
        match = None
        for m in HEADING_RE.finditer(sub):
            if m.group(2).strip() == heading:
                match = m
                break
        if match:
            abs_pos = cursor + match.start()
            positions.append((abs_pos, s))
            cursor = abs_pos + len(match.group(0))
        else:
            positions.append((-1, s))

    # Build chunks
    chunks: list[tuple[dict, str]] = []
    sorted_positions = [(p, s) for p, s in positions if p >= 0]
    sorted_positions.sort(key=lambda x: x[0])

    pos_to_next = {}
    for i, (p, _) in enumerate(sorted_positions):
        next_p = sorted_positions[i + 1][0] if i + 1 < len(sorted_positions) else len(markdown_text)
        pos_to_next[p] = next_p

    for p, s in positions:
        if p < 0:
            chunks.append((s, ""))
        else:
            chunk = markdown_text[p:pos_to_next[p]]
            chunks.append((s, chunk))
    return chunks


def inline_local_images(html: str, md_dir: Path) -> str:
    """Find <img src="..."> with non-URL src and inline as base64 data URI."""
    def repl(match: re.Match) -> str:
        src = match.group(1)
        parsed = urlparse(src)
        if parsed.scheme in ("http", "https", "data"):
            return match.group(0)
        candidate = (md_dir / src).resolve() if not Path(src).is_absolute() else Path(src)
        if not candidate.exists() or not candidate.is_file():
            alt = re.search(r'alt="([^"]*)"', match.group(0))
            placeholder = f'[image not found: {alt.group(1) if alt else src}]'
            return f'<span class="callout callout--note"><span class="callout__icon">🖼</span><div class="callout__body">{placeholder}</div></span>'
        mime = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
        new_src = f"data:{mime};base64,{encoded}"
        return match.group(0).replace(f'src="{src}"', f'src="{new_src}"')

    return re.sub(r'<img[^>]*\ssrc="([^"]+)"[^>]*>', repl, html)


MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def extract_mermaid(markdown_text: str) -> tuple[str, list[str]]:
    """Pull ```mermaid blocks out of the markdown so they don't get code-highlighted.

    Returns (markdown_with_placeholders, list_of_diagrams).
    Placeholders are HTML <pre class="mermaid"> blocks that markdown lib will pass through.
    """
    diagrams: list[str] = []

    def repl(m: re.Match) -> str:
        diagrams.append(m.group(1).strip())
        return f'\n\n<figure class="mermaid-wrap"><pre class="mermaid">{m.group(1).strip()}</pre></figure>\n\n'

    new_md = MERMAID_BLOCK_RE.sub(repl, markdown_text)
    return new_md, diagrams


def render_markdown_chunk(chunk: str) -> str:
    if not chunk.strip():
        return ""
    md = md_lib.Markdown(
        extensions=[
            "extra",
            "sane_lists",
            "tables",
            "fenced_code",
            "admonition",
            "attr_list",
            "def_list",
            "toc",
            CodeHiliteExtension(guess_lang=False, css_class="hljs", noclasses=False),
        ],
        output_format="html5",
    )
    return md.convert(chunk)


def wrap_code_blocks(html: str) -> str:
    """Wrap pygments code blocks with header + copy button container."""
    def repl(match: re.Match) -> str:
        block = match.group(0)
        # Try to detect language from class
        lang_match = re.search(r'class="[^"]*language-([a-zA-Z0-9_+\-]+)', block)
        lang = lang_match.group(1) if lang_match else "code"
        return (
            f'<div class="code-block">'
            f'<div class="code-block__header">'
            f'<span class="code-block__lang">{lang}</span>'
            f'<button class="code-block__copy">Copy</button>'
            f'</div>'
            f'{block}'
            f'</div>'
        )

    return re.sub(r"<pre[^>]*>.*?</pre>", repl, html, flags=re.DOTALL)


def sanitize(html: str) -> str:
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )


SKIP_PROTECT_PATTERNS = [
    re.compile(r"<pre[\s\S]*?</pre>", re.IGNORECASE),
    re.compile(r"<code[\s\S]*?</code>", re.IGNORECASE),
    re.compile(r"<h[1-6][\s\S]*?</h[1-6]>", re.IGNORECASE),
    re.compile(r'<a\b[\s\S]*?</a>', re.IGNORECASE),
    re.compile(r'<span class="gloss"[\s\S]*?</span></span>'),
]
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
PLACEHOLDER_RE = re.compile(r"@@GLOSS_SKIP_(\d+)@@")


def _build_tooltip_html(plain: str, analogy: str) -> str:
    """Build the <span class='gloss__tip'> body. Metadata strings are escaped."""
    plain_esc = html_lib.escape(plain or "")
    parts = [
        '<span class="gloss__tip" role="tooltip">',
        '<span class="gloss__tip-label">Plain</span>',
        plain_esc,
    ]
    if analogy:
        parts.append('<span class="gloss__tip-label gloss__tip-label--alt">Analogy</span>')
        parts.append(html_lib.escape(analogy))
    parts.append('</span>')
    return "".join(parts)


def insert_glossary_terms(html: str, concepts: list[dict]) -> str:
    """Wrap every plain-text occurrence of every glossary term with a hover tooltip span.

    Skips occurrences inside <pre>, <code>, headings, <a>, and existing .gloss wrappers.
    Term matching is case-sensitive with word-boundary checks so that "API" won't match
    inside "rAPID". Longer terms are processed first so they aren't eaten by shorter ones.
    """
    if not concepts:
        return html

    sorted_concepts = sorted(
        (c for c in concepts if c.get("term", "").strip()),
        key=lambda c: len(c["term"]),
        reverse=True,
    )

    for c in sorted_concepts:
        term = c["term"].strip()
        tip_html = _build_tooltip_html(c.get("plain_explanation", ""), c.get("analogy", ""))

        # Stash regions we never want to touch
        stash: list[str] = []

        def stash_sub(m: re.Match) -> str:
            stash.append(m.group(0))
            return f"@@GLOSS_SKIP_{len(stash) - 1}@@"

        protected = html
        for pat in SKIP_PROTECT_PATTERNS:
            protected = pat.sub(stash_sub, protected)

        # Build term regex with word-boundary guards that work for non-ASCII too.
        # \b in re module is ASCII-only; use lookarounds against \w and the term endpoints.
        first, last = term[0], term[-1]
        left_guard = r"(?<!\w)" if first.isalnum() or first == "_" else ""
        right_guard = r"(?!\w)" if last.isalnum() or last == "_" else ""
        term_re = re.compile(left_guard + re.escape(term) + right_guard)

        def wrap(m: re.Match) -> str:
            return (
                f'<span class="gloss" tabindex="0" role="button" '
                f'aria-label="glossary: {html_lib.escape(term)}">'
                f'{m.group(0)}{tip_html}</span>'
            )

        # Walk text portions vs tag portions; only replace within text.
        parts = TAG_SPLIT_RE.split(protected)
        for i in range(0, len(parts), 2):
            if parts[i]:
                parts[i] = term_re.sub(wrap, parts[i])
        protected = "".join(parts)

        # Restore stashed regions
        html = PLACEHOLDER_RE.sub(lambda m: stash[int(m.group(1))], protected)

    return html


_SCRIPT_BLOCK_RE = re.compile(r"<script\b[\s\S]*?</script>", re.IGNORECASE)
_STYLE_BLOCK_RE = re.compile(r"<style\b[\s\S]*?</style>", re.IGNORECASE)


def sanitize_svg(svg_str: str) -> str:
    """Strip script/style tags + content, event handlers, and disallowed attrs from an
    LLM-supplied SVG. Bleach alone would strip <script> but keep its inner text — we don't
    want raw `alert('xss')` showing as visible text inside the hero.
    """
    cleaned = _SCRIPT_BLOCK_RE.sub("", svg_str)
    cleaned = _STYLE_BLOCK_RE.sub("", cleaned)
    return bleach.clean(
        cleaned,
        tags=SVG_ALLOWED_TAGS,
        attributes=SVG_ALLOWED_ATTRS,
        protocols=SVG_ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )


def build_hero_image_html(meta: dict, md_dir: Path) -> str:
    """Return inline HTML for the hero image, or '' if none."""
    svg = (meta.get("hero_image_svg") or "").strip()
    path_str = (meta.get("hero_image_path") or "").strip()

    if path_str:
        p = Path(path_str)
        if not p.is_absolute():
            p = (md_dir / path_str).resolve()
        if p.exists() and p.is_file():
            mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
            data = base64.b64encode(p.read_bytes()).decode("ascii")
            alt = html_lib.escape(meta.get("title", "Report hero image"))
            if mime == "image/svg+xml":
                # Inline SVG for nicer scaling / theming
                try:
                    return sanitize_svg(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
            return f'<img src="data:{mime};base64,{data}" alt="{alt}" />'

    if svg:
        return sanitize_svg(svg)

    return ""


def build(
    markdown_path: Path,
    metadata_path: Path,
    output_path: Path,
    image_base_dir: Path | None = None,
) -> Path:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    meta = read_metadata(metadata_path)

    # Relative image paths in the markdown body resolve against image_base_dir.
    # Defaults to the markdown file's own folder, but when the source is a temp
    # file (pasted string / chat-produced markdown) the caller must pass the
    # ORIGINAL markdown_dir here, otherwise relative images won't be found.
    img_base = image_base_dir or markdown_path.parent

    # Sectionize the ORIGINAL markdown. These slices are only used as a fallback
    # for sections that don't supply a rewritten `body_markdown`. Mermaid blocks
    # are pulled out per-section below (after the body source is chosen), so the
    # rewritten-prose path and the legacy slice path get identical treatment.
    chunks = split_markdown_by_sections(markdown_text, meta["sections"])

    # Build per-section blocks
    section_blocks = []
    section_callouts: dict[str, list[dict]] = {}
    for c in meta["callouts"]:
        section_callouts.setdefault(c["section_id"], []).append(c)
    section_diagrams: dict[str, list[dict]] = {}
    for d in meta["auto_diagrams"]:
        section_diagrams.setdefault(d["after_section_id"], []).append(d)

    for s_meta, chunk in chunks:
        # Prefer the LLM's rewritten prose body. Fall back to the verbatim slice
        # of the source markdown (heading line stripped — the template renders it).
        body_md = (s_meta.get("body_markdown") or "").strip()
        if body_md:
            body_source = body_md
        else:
            body_source = HEADING_RE.sub("", chunk, count=1) if chunk else ""
        # Pull mermaid fences out so they aren't code-highlighted (applies to both
        # the rewritten body and the legacy slice).
        body_source, _ = extract_mermaid(body_source)
        rendered = render_markdown_chunk(body_source)
        rendered = inline_local_images(rendered, img_base)
        rendered = wrap_code_blocks(rendered)
        # Sanitize untrusted markdown-rendered HTML first, THEN inject our own
        # controlled glossary tooltip spans (whose payload is html-escaped metadata).
        rendered = sanitize(rendered)
        rendered = insert_glossary_terms(rendered, meta["concepts"])
        section_blocks.append({
            "meta": s_meta,
            "html": rendered,
            "callouts": section_callouts.get(s_meta["id"], []),
            "diagrams": section_diagrams.get(s_meta["id"], []),
        })

    hero_image_html = build_hero_image_html(meta, img_base)

    # Detect mermaid usage
    has_mermaid = bool(meta["auto_diagrams"]) or any(
        '<pre class="mermaid">' in b["html"] for b in section_blocks
    ) or any(b["diagrams"] for b in section_blocks)

    # Detect code blocks (for highlight.js inclusion)
    has_code = any('<pre' in b["html"] for b in section_blocks)

    # Load assets
    magazine_css = (STYLES_DIR / "magazine.css").read_text(encoding="utf-8")
    highlight_light_css = (VENDOR_DIR / "highlight-github.min.css").read_text(encoding="utf-8")
    highlight_dark_css = (VENDOR_DIR / "highlight-github-dark.min.css").read_text(encoding="utf-8")
    highlight_js = (VENDOR_DIR / "highlight.min.js").read_text(encoding="utf-8") if has_code else ""
    mermaid_js = (VENDOR_DIR / "mermaid.min.js").read_text(encoding="utf-8") if has_mermaid else ""

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    tmpl = env.get_template("report.html.j2")
    html = tmpl.render(
        meta=meta,
        section_blocks=section_blocks,
        icons=ICONS,
        callout_icons=CALLOUT_ICONS,
        magazine_css=magazine_css,
        highlight_light_css=highlight_light_css,
        highlight_dark_css=highlight_dark_css,
        highlight_js=highlight_js,
        mermaid_js=mermaid_js,
        include_mermaid=has_mermaid,
        include_highlight=has_code,
        hero_image_html=hero_image_html,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--image-base",
        type=Path,
        default=None,
        help="Base directory for resolving relative image paths in the markdown "
        "body. Defaults to the markdown file's folder; pass the ORIGINAL "
        "markdown_dir when the markdown source is a temp file (pasted string or "
        "chat-produced content) so relative images still resolve.",
    )
    args = parser.parse_args()

    if not args.markdown.exists():
        print(f"ERROR: markdown not found: {args.markdown}", file=sys.stderr)
        sys.exit(1)
    if not args.metadata.exists():
        print(f"ERROR: metadata not found: {args.metadata}", file=sys.stderr)
        sys.exit(1)

    out = build(args.markdown, args.metadata, args.output, image_base_dir=args.image_base)
    print(str(out))


if __name__ == "__main__":
    main()
