# MDknowledge — reference knowledge for the agent

Theme folders live here (`programming/python/`, `geography/`, ...).
At startup the agent ingests them into searchable memory; matching facts
are recalled into context per turn. This is reference context, not instructions.

## Authoring rules

- One fact per bullet: lines starting with `- ` (12+ chars) are ingested.
- Headings, prose, and fenced code blocks are skipped — put the fact in the bullet.
- Keep bullets self-contained: include the language/topic in the bullet when ambiguous.
- Files named `README.md` or starting with `_` (e.g. `_template.md`) are never ingested.
- User-local override: `~/.hellochusquis/knowledge/<same/relative/path.md>` wins over the repo file.

## Layout

- `programming/<language>/<topic>.md` — e.g. `programming/python/lists.md`
- `<theme>/<topic>.md` — e.g. `geography/europe-capitals.md`
- Copy the nearest `_template.md` when adding a new file.
