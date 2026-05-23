---
name: ab-review
description: Use when the user explicitly asks for an "AB", adversarial, two-sided, or "red-team" code review of code changes they have made — e.g. "AB review my diff", "do an AB review of my changes", "red-team this code change", "have two reviewers argue about my code". Dispatches two opposing sub-agents — one building the evidence-based case that the change is mergeable, one building the case that it must not merge — runs them in parallel, and returns both reports to the main agent to judge. The skill itself never issues the verdict. Manual-trigger only — never auto-invoke; always ask the user to choose the review scope first. Skip for a routine single-perspective code review.
---

# AB Review

Two sub-agents with opposing assigned stances independently review the **same**
code change and report concrete evidence. One argues the change is mergeable,
the other argues it is not. The main agent then reads both reports and forms
its own judgment.

A single-perspective review tends to anchor on one read of a change. Forcing
one agent to build the strongest case *for* merging and another to build the
strongest case *against* surfaces both the strengths and the risks a one-sided
pass would miss — and leaves the final call to the main agent with both cases
in hand.

## When to invoke

- **Manual only.** The user explicitly asks for an AB / adversarial /
  two-sided / red-team review of their code changes.
- **Never auto-invoke.** Dispatching two sub-agents is expensive; wait for an
  explicit request.
- The skill and the sub-agents **never pronounce the final verdict** — that is
  the main agent's job (Step 5).

## Workflow

### Step 1 — Confirm the review scope (always ask)

Before doing anything else, use `AskUserQuestion` to ask the user which code
change to review. Offer these options:

1. **All unstaged changes** — `git diff`
2. **Latest commit** — `git show HEAD`
3. **All commits on the current feature branch** — `git diff main...HEAD`
4. **Specific lines of code** — then ask the user for file path(s) and line
   range(s)

Do not guess the scope. If the working directory is not a git repository, stop
and tell the user.

### Step 2 — Capture the code change once

Run the git command for the chosen scope and capture the diff text **once** —
the identical text is handed to both sub-agents so they argue about the same
artifact.

- For scope 4, capture the specified line ranges with a few lines of
  surrounding context.
- For scope 1, also list untracked files (`git diff` does not show them) and
  include their contents if they are relevant to the change.
- If the chosen scope yields no changes, tell the user there is nothing to
  review and stop.

### Step 3 — Dispatch the two reviewers in parallel

In a **single message**, make two `Agent` calls dispatching the plugin's
bundled reviewer agents:

- `subagent_type: ab-review-pro` — argues the change is correct and mergeable.
- `subagent_type: ab-review-con` — argues the change is flawed and must not merge.

They run independently and in parallel; neither sees the other's findings. Each
agent already carries its assigned stance, tool boundaries, the no-fabrication
rule, and the required report format — defined in `agents/ab-review-pro.md` and
`agents/ab-review-con.md`. Do not re-specify any of that here.

Pass **both** agents the same task prompt:

- the captured code change from Step 2 (the identical text for both),
- the review scope chosen in Step 1,
- the repository path, so the agent can read surrounding code for context.

### Step 4 — What each reviewer returns

Each agent returns a structured report (canonical format defined in its agent
file): its side, a one-line position, numbered evidence items — each with a
`file:line` location, a verbatim code snippet, an argument, and a strength
rating — its single strongest point, and an honest statement of where its own
side is weakest.

### Step 5 — Judge (main agent)

After both reports return, the main agent — **not a sub-agent, not the skill** —
does the judging. Present to the user:

1. The review scope that was reviewed.
2. Pro's strongest evidence and Con's strongest evidence — concise, pointing to
   `file:line`.
3. The main agent's own independent judgment: which evidence holds up under
   scrutiny (verify the cited code directly if in doubt), and where the two
   sides genuinely disagree.
4. A clear recommendation — merge as-is / merge after specific fixes / do not
   merge — with concrete action items.

Do not merely average the two sides; weigh the evidence. If a side cited
something that does not hold up, say so.

## Notes

- No dependencies and no script — git plus the `Agent` tool only.
- The two reviewers are bundled plugin agents (`ab-review-pro`, `ab-review-con`,
  in `agents/`); they are review-only, with read-only file and git access.
- Always exactly two sub-agents: one Pro, one Con.
- The skill never writes files or changes code; it is review-only.
- If the final write-up is long, the `markdown-to-html-report` skill may
  naturally apply for presenting it — optional and separate.
