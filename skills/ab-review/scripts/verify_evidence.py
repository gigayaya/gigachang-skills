#!/usr/bin/env python3
"""verify_evidence.py — check that ab-review evidence citations are real.

The two ab-review sub-agents (`ab-review-pro`, `ab-review-con`) are advocates:
each is assigned a stance and builds the strongest case for it. To keep the
adversarial review honest rather than performative, every evidence item carries
a `file` + `line` + verbatim `snippet`. This script greps each snippet against
the repository and reports whether it actually exists, so the main agent judges
on verified citations instead of taking either advocate at its word.

Standard library only — no install step.

Input: one or more JSON files, each a list of evidence objects (or an object
with an `"evidence"` list). Each object has the shape produced by the agents:

    {"id": "E1", "side": "PRO|CON", "file": "path", "line": "42" | "40-45",
     "snippet": "verbatim code", "strength": "strong|moderate|weak"}

CLI:
    python verify_evidence.py --repo <repo_path> <evidence.json> [<evidence2.json> ...]

For each item the script prints VERIFIED / SNIPPET_NOT_FOUND / FILE_NOT_FOUND /
NO_SNIPPET, then a summary. Exit code is non-zero when any *strong* item fails
verification — a strong claim whose snippet isn't in the repo is the single most
important thing for the main agent to discount.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_items(paths):
    """Load evidence objects from one or more JSON files.

    Each file may be a bare list or an object with an "evidence" list. Returns a
    flat list of (source_file, item_dict). Malformed files are reported, skipped.
    """
    items = []
    for p in paths:
        path = Path(p)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARN: could not read evidence JSON {path}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            data = data.get("evidence", [])
        if not isinstance(data, list):
            print(f"WARN: {path} is not a list of evidence items — skipped", file=sys.stderr)
            continue
        for obj in data:
            if isinstance(obj, dict):
                items.append((path.name, obj))
    return items


_DIFF_PREFIX_RE = re.compile(r"^[+\-]\s?")
_WS_RE = re.compile(r"\s+")


def normalize(text):
    """Collapse code to a whitespace-insensitive form for tolerant matching.

    Drops leading diff markers (`+`/`-`) per line, then flattens all runs of
    whitespace (including newlines) to single spaces. This lets a multi-line
    snippet match the file even if indentation or line wrapping differs slightly.
    """
    lines = [_DIFF_PREFIX_RE.sub("", ln) for ln in text.splitlines()]
    return _WS_RE.sub(" ", " ".join(lines)).strip()


def resolve_file(repo, rel):
    """Resolve an evidence `file` against the repo root. Returns a Path or None."""
    if not rel:
        return None
    candidate = Path(rel)
    if not candidate.is_absolute():
        candidate = (repo / rel).resolve()
    if candidate.exists() and candidate.is_file():
        return candidate
    # Fall back to a basename search inside the repo (agents sometimes cite a
    # path relative to a subdir). Only accept a unique match.
    matches = [m for m in repo.rglob(Path(rel).name) if m.is_file()]
    if len(matches) == 1:
        return matches[0]
    return None


def verify_item(repo, item):
    """Return (status, detail) for one evidence item.

    status is one of VERIFIED, SNIPPET_NOT_FOUND, FILE_NOT_FOUND, NO_SNIPPET.
    """
    snippet = (item.get("snippet") or "").strip()
    if not snippet:
        return "NO_SNIPPET", "no snippet supplied"

    file_path = resolve_file(repo, item.get("file", ""))
    if file_path is None:
        return "FILE_NOT_FOUND", f"file not found: {item.get('file', '?')}"

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return "FILE_NOT_FOUND", f"could not read {file_path}: {exc}"

    if normalize(snippet) in normalize(content):
        return "VERIFIED", str(file_path)
    return "SNIPPET_NOT_FOUND", f"snippet not present in {item.get('file', '?')}"


STATUS_ICON = {
    "VERIFIED": "✓",          # check mark
    "SNIPPET_NOT_FOUND": "✗", # ballot x
    "FILE_NOT_FOUND": "✗",
    "NO_SNIPPET": "—",        # em dash
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Repository root to check citations against.")
    parser.add_argument("evidence", nargs="+", help="One or more evidence JSON files.")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"ERROR: --repo is not a directory: {repo}", file=sys.stderr)
        sys.exit(2)

    items = load_items(args.evidence)
    if not items:
        print("No evidence items found to verify.")
        sys.exit(0)

    failed_strong = []
    counts = {"VERIFIED": 0, "SNIPPET_NOT_FOUND": 0, "FILE_NOT_FOUND": 0, "NO_SNIPPET": 0}

    print("Evidence verification")
    print("=" * 60)
    for src, item in items:
        status, detail = verify_item(repo, item)
        counts[status] = counts.get(status, 0) + 1
        side = item.get("side", "?")
        ident = item.get("id", "?")
        strength = (item.get("strength") or "?").lower()
        line = item.get("line", "?")
        icon = STATUS_ICON.get(status, "?")
        print(f"{icon} [{side} {ident}] strength={strength} {item.get('file', '?')}:{line}")
        print(f"    {status} — {detail}")
        if status in ("SNIPPET_NOT_FOUND", "FILE_NOT_FOUND") and strength == "strong":
            failed_strong.append((side, ident, item.get("file", "?"), line))

    print("=" * 60)
    print(
        f"Summary: {counts['VERIFIED']} verified, "
        f"{counts['SNIPPET_NOT_FOUND']} snippet-not-found, "
        f"{counts['FILE_NOT_FOUND']} file-not-found, "
        f"{counts['NO_SNIPPET']} no-snippet "
        f"(of {len(items)} items)."
    )
    if failed_strong:
        print()
        print("WARNING: strong evidence that FAILED verification (discount heavily):")
        for side, ident, f, line in failed_strong:
            print(f"  - [{side} {ident}] {f}:{line}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
