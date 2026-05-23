---
description: Research the scope of a requirement against the current codebase and report the facts
argument-hint: "[requirement description, file path to a spec, or leave empty to use chat context]"
---

Invoke the `scope-research` skill to survey the codebase against a proposed requirement and return a structured fact report — affected areas/files and the relevant facts about each touchpoint.

Requirement: $ARGUMENTS

If no argument is given, use the requirement the user has described in this conversation. Ask clarifying questions before exploring if anything material is unclear. Do not issue a verdict (no t-shirt size, no LOC estimate, no time estimate, no risk rating) — state facts only.
