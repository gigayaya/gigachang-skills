# General rules

General-purpose rules that apply to every file in this repository. Read this
before writing any new file, comment, or commit message.

Each rule is structured as three sections:

- **Description** — what the rule says.
- **Detect** — how to find a violation (visual cues, commands, signals).
- **Fix** — how to bring a violation back into compliance.

## GR-1. English only

### Description

All content in this repository — code, comments, documentation, skill
`description` fields, YAML frontmatter, examples, and commit messages — must
be written in English. This also applies to plan files and any other Markdown
checked into the repo. The only acceptable exception is verbatim quotation of
a non-English source (e.g. quoting a user's original wording inside a plan);
in that case the quote must be enclosed in quotation marks and accompanied by
an English summary.

### Detect

- **Visual check while writing or reviewing**: scan the diff for any CJK,
  Hiragana, Katakana, or Hangul characters.
- **Single file or directory scan**:
  ```
  rg -nP '[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]' <path>
  ```
  An empty result means the path is clean.
- **Recent commit messages**:
  ```
  git log -n 20 --pretty=%s%n%b | rg -P '[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]'
  ```
- **Common hot spots to inspect**: skill `description:` frontmatter fields,
  `README.md` table rows, slash command frontmatter, code comments, and any
  new Markdown under `docs/`.

### Fix

- Translate the offending text into natural, concise English. Do not
  translate word-for-word; rephrase so the English reads idiomatically.
- Code identifiers that are already English stay as they are; only string
  literals, comments, and documentation need rewriting.
- When the non-English text is a genuine quotation (e.g. a plan referencing
  the user's original request), keep the original wording in quotation marks
  and add an English paraphrase or summary around it.
- For commit messages: if the commit has not been pushed, use
  `git commit --amend` to rewrite it. If it is already pushed, do not
  force-push to rewrite history; instead, add a follow-up commit whose
  message references and corrects the earlier one.

## GR-2. Update the skill catalog when adding a skill

### Description

After adding a new skill under `skills/<skill-name>/`, also update every
catalog that lists skills so the new one is discoverable:

- Create `docs/knowledge/skills/<skill-name>-index.md` and add a row pointing
  to it in the **Per-skill indexes** table in `docs/knowledge/codemap.md`.
- Add a row describing the skill in the **Skills in this plugin** table in
  `README.md`.
- If the skill ships a matching slash command under `commands/`, also add a
  row to the **Slash commands** table in `README.md`.

### Detect

- **List what is actually on disk**:
  ```
  ls skills/
  ls commands/
  ```
- **Per-skill index exists**:
  ```
  ls docs/knowledge/skills/<skill-name>-index.md
  ```
- **Catalog mentions the skill**:
  ```
  grep -l "<skill-name>" docs/knowledge/codemap.md README.md
  ```
  Both files should appear in the output. If either is missing, the catalog
  is out of sync.
- **Slash command is listed when applicable**: if `commands/<skill-name>.md`
  exists, confirm the **Slash commands** table in `README.md` mentions it
  with `grep "<skill-name>" README.md`.

### Fix

- **Missing per-skill index**: copy an existing one such as
  `docs/knowledge/skills/ab-review-index.md` as a template, then save the
  new file at `docs/knowledge/skills/<skill-name>-index.md` and replace its
  contents to describe the new skill.
- **Missing row in `docs/knowledge/codemap.md`**: append a row to the
  **Per-skill indexes** table in the form
  `| <skill-name> | [skills/<skill-name>-index.md](skills/<skill-name>-index.md) | <one-line what it does> |`.
- **Missing row in `README.md` Skills table**: append a row describing the
  skill in the same column shape as the existing rows.
- **Missing row in `README.md` Slash commands table**: if a matching
  `commands/<skill-name>.md` exists, append a row pointing at it.
- **Version bump**: per the user's global rules, bump
  `.claude-plugin/plugin.json` in the same commit as the skill addition.
  Adding a skill counts as a new feature, so apply a minor bump.
