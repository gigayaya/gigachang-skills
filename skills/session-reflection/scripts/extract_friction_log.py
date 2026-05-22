#!/usr/bin/env python3
"""extract_friction_log.py — distill a Claude Code session transcript into a
compact "friction log".

A raw session transcript (`~/.claude/projects/<encoded-cwd>/<session>.jsonl`)
is large and noisy: thinking blocks, base64 attachments, full tool-result
dumps. The `session-reflection` skill only needs the *shape* of the
conversation — what the user asked, what Claude did, and where things were
rejected or errored. This script extracts exactly that into a numbered
timeline, flagging every rejection (`<<REJECTED>>`) and error (`<<ERROR>>`)
so the LLM can locate the back-and-forth without reading the whole JSONL.

Standard library only — no install step.

CLI:
    python extract_friction_log.py [--transcript PATH] [--out PATH]

With no --transcript, the current session's transcript is auto-detected by
matching each candidate's recorded `cwd` against the current directory and
picking the most-recently-modified match (the live session is always newest).
The output file path is printed to stdout.
"""

import argparse
import glob
import json
import os
import sys
import tempfile

# Substrings that identify a tool_result produced by the user rejecting a
# tool call (as opposed to the tool itself failing).
REJECTION_MARKERS = (
    "doesn't want to proceed with this tool use",
    "tool use was rejected",
)

# Record types that carry no friction signal — skipped wholesale.
SKIP_TYPES = {
    "last-prompt",
    "permission-mode",
    "ai-title",
    "agent-name",
    "file-history-snapshot",
    "attachment",
}

# Tool-input keys worth surfacing, in priority order.
INPUT_KEYS = (
    "command",
    "file_path",
    "path",
    "pattern",
    "query",
    "url",
    "skill",
    "description",
    "prompt",
    "old_string",
)


def trunc(text, limit):
    """Collapse whitespace runs lightly and cap length with an ellipsis note."""
    text = "" if text is None else str(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + " ...[%d more chars]" % (len(text) - limit)


def oneline(text):
    """Flatten to a single line for compact inline display."""
    return " ".join(str(text).split())


def load_records(path):
    """Parse a JSONL transcript, skipping blank and unparseable lines (the
    final line of a live session may be a partial write)."""
    records = []
    try:
        handle = open(path, encoding="utf-8", errors="replace")
    except OSError as exc:
        sys.exit("could not open transcript: %s" % exc)
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                records.append(obj)
    return records


def peek_cwd(path, max_lines=60):
    """Return the `cwd` recorded in a transcript, or None."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index >= max_lines:
                    break
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("cwd"):
                    return obj["cwd"]
    except OSError:
        pass
    return None


def find_transcript(explicit, cwd):
    """Resolve which transcript to read."""
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit("transcript file not found: %s" % explicit)
        return explicit

    pattern = os.path.join(
        os.path.expanduser("~"), ".claude", "projects", "*", "*.jsonl"
    )
    matches = [p for p in glob.glob(pattern) if peek_cwd(p) == cwd]
    if not matches:
        sys.exit(
            "could not auto-detect a session transcript for cwd=%s\n"
            "Pass one explicitly with --transcript "
            "<~/.claude/projects/.../<session-id>.jsonl>" % cwd
        )
    return max(matches, key=os.path.getmtime)


def blocks_to_text(content):
    """Flatten a message `content` (str or list of blocks) to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "image":
                    parts.append("[image]")
                elif "text" in block:
                    parts.append(block.get("text") or "")
        return "\n".join(p for p in parts if p)
    return str(content)


def summarize_tool_input(inp):
    """One-line summary of a tool_use input dict."""
    if not isinstance(inp, dict) or not inp:
        return oneline(trunc(inp, 200))
    for key in INPUT_KEYS:
        value = inp.get(key)
        if value:
            return "%s: %s" % (key, oneline(trunc(value, 240)))
    key, value = next(iter(inp.items()))
    return "%s: %s" % (key, oneline(trunc(value, 240)))


def classify_result(text, is_error):
    """Return 'REJECTED', 'ERROR', or '' for a tool_result."""
    low = text.lower()
    if any(marker in low for marker in REJECTION_MARKERS):
        return "REJECTED"
    if is_error:
        return "ERROR"
    return ""


def build_events(records):
    """Walk records in chronological (file) order into a flat event list."""
    events = []
    tool_names = {}  # tool_use_id -> tool name, for labelling results

    for obj in records:
        rec_type = obj.get("type")
        if rec_type in SKIP_TYPES or obj.get("isSidechain"):
            continue

        if rec_type == "system":
            content = oneline(blocks_to_text(obj.get("content")))
            if not content:
                continue
            flag = ""
            if obj.get("preventedContinuation") or obj.get("hookErrors"):
                flag = "ERROR"
            events.append(
                {"kind": "system", "flag": flag, "text": trunc(content, 400)}
            )
            continue

        message = obj.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")

        if rec_type == "user":
            if obj.get("isMeta"):
                events.append(
                    {
                        "kind": "meta",
                        "flag": "",
                        "text": "[harness/system-reminder injected — omitted]",
                    }
                )
                continue
            blocks = content if isinstance(content, list) else []
            # Tool results carried back on the user turn.
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    text = blocks_to_text(block.get("content"))
                    flag = classify_result(text, block.get("is_error"))
                    name = tool_names.get(block.get("tool_use_id"), "tool")
                    limit = 700 if flag else 200
                    events.append(
                        {
                            "kind": "result",
                            "flag": flag,
                            "tool": name,
                            "text": trunc(oneline(text), limit),
                        }
                    )
            # Genuine user prompt text.
            prompt = oneline(blocks_to_text(content))
            if prompt:
                events.append(
                    {"kind": "user", "flag": "", "text": trunc(prompt, 1200)}
                )
            continue

        if rec_type == "assistant":
            blocks = content if isinstance(content, list) else []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    text = oneline(block.get("text") or "")
                    if text:
                        events.append(
                            {"kind": "assistant", "flag": "", "text": trunc(text, 600)}
                        )
                elif btype == "tool_use":
                    name = block.get("name") or "tool"
                    tool_names[block.get("id")] = name
                    events.append(
                        {
                            "kind": "tool_use",
                            "flag": "",
                            "tool": name,
                            "text": summarize_tool_input(block.get("input")),
                        }
                    )
    return events


def render(events, transcript_path):
    """Render the friction-log markdown."""
    counts = {
        "user": sum(1 for e in events if e["kind"] == "user"),
        "tool_use": sum(1 for e in events if e["kind"] == "tool_use"),
        "rejected": sum(1 for e in events if e["flag"] == "REJECTED"),
        "errored": sum(1 for e in events if e["flag"] == "ERROR"),
    }

    lines = [
        "# Session Friction Log",
        "",
        "Source transcript: `%s`" % transcript_path,
        "",
        "## Summary",
        "",
        "- User prompts: %d" % counts["user"],
        "- Tool calls: %d" % counts["tool_use"],
        "- Rejected tool calls (`<<REJECTED>>`): %d" % counts["rejected"],
        "- Errored tool results (`<<ERROR>>`): %d" % counts["errored"],
        "",
        "Rejections and errors are friction points: outputs the user refused "
        "or that failed. User prompts that follow Claude's work may also be "
        "corrections — judge each from its wording.",
        "",
        "## Timeline",
        "",
    ]

    if not events:
        lines.append("_(no conversational events found in this transcript)_")
    for index, event in enumerate(events, 1):
        flag = (" <<%s>>" % event["flag"]) if event["flag"] else ""
        kind = event["kind"]
        if kind == "user":
            label = "USER"
        elif kind == "assistant":
            label = "ASSISTANT"
        elif kind == "tool_use":
            label = "ASSISTANT -> %s" % event["tool"]
        elif kind == "result":
            label = "RESULT (%s)" % event["tool"]
        elif kind == "system":
            label = "SYSTEM"
        else:
            label = "META"
        lines.append("%d. [%s]%s %s" % (index, label, flag, event["text"]))

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Distill a Claude Code session transcript into a "
        "compact friction log for the session-reflection skill."
    )
    parser.add_argument(
        "--transcript",
        help="Path to a session .jsonl transcript. "
        "Default: auto-detect the current session by cwd + mtime.",
    )
    parser.add_argument(
        "--out",
        help="Output path for the friction log. Default: a temp .md file.",
    )
    args = parser.parse_args()

    transcript = find_transcript(args.transcript, os.getcwd())
    records = load_records(transcript)
    events = build_events(records)
    report = render(events, transcript)

    out_path = args.out
    if not out_path:
        handle, out_path = tempfile.mkstemp(
            prefix="friction-log-", suffix=".md"
        )
        os.close(handle)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(report)

    print(os.path.abspath(out_path))


if __name__ == "__main__":
    main()
