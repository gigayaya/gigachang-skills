# adversarial-code-review

A two-sided **"AB" code review**. After you finish a task and make code
changes, invoke this skill to get an adversarial review: Claude dispatches two
opposing sub-agents — a **Pro** reviewer arguing the change is mergeable and a
**Con** reviewer arguing it is not — each required to back its position with
concrete evidence pulled from the actual diff. Both reports come back to the
main agent, which then forms its **own** judgment. The skill itself never
issues the verdict.

A single-perspective review tends to anchor on one read of a change. Splitting
it into a strongest-case-for and a strongest-case-against surfaces both the
strengths and the risks a one-sided pass would miss.

Triggered manually when you ask Claude for an adversarial / AB / two-sided /
red-team review of your changes. It never auto-runs.

## How Claude uses it

1. **Confirms the review scope** — Claude always asks first which code change
   to review: all unstaged changes, the latest commit, all commits on the
   feature branch, or specific lines of code.
2. **Captures the diff once** — runs the matching git command and freezes the
   diff text so both reviewers argue about the identical artifact.
3. **Dispatches two reviewer agents in parallel** — `ab-review-pro` (argues the
   change is mergeable) and `ab-review-con` (argues it is not). These are
   bundled plugin agents defined in the plugin's `agents/` directory; each
   carries its own stance, tool boundaries, and report format. They run
   independently; neither sees the other's findings.
4. **Collects two structured reports** — each sub-agent reports its evidence in
   a fixed format (claim, `file:line` location, verbatim code, argument,
   strength), plus its strongest point and the honest weakness of its own side.
5. **Judges** — the main agent reads both reports, weighs the evidence (it does
   not just average the two sides), and presents its own recommendation with
   concrete action items.

Unlike the sibling skills in this plugin, this one is **pure orchestration** —
its core work is dispatching and coordinating sub-agents, so there is no
transformation script. Claude runs git directly.

## Required dependencies

**None.** The skill uses `git` and the `Agent` tool only — no `pip install`
step and no runtime script.

## File layout

```
adversarial-code-review/
├── SKILL.md     # skill description + workflow
└── README.md    # this file
```

## Notes

- Manual-trigger only — Claude never auto-invokes it.
- The skill and its sub-agents never pronounce the final verdict; the main
  agent makes the call after reading both reports.
- It is review-only — it never writes files or changes code.
