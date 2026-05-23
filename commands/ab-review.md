---
description: Two opposing sub-agents review the same diff (pro-merge vs. block-merge), main agent judges
argument-hint: "[optional scope, e.g. 'staged changes', 'PR #42', or a path]"
---

Invoke the `ab-review` skill on the user's code change.

Scope (if provided): $ARGUMENTS

Per the skill: always confirm the review scope with the user first, dispatch the two opposing sub-agents in parallel, then read both reports and form the final judgment yourself.
