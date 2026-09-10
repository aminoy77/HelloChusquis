# SQL triggers

- In SQL, triggers fire automatically on INSERT/UPDATE/DELETE events.
- In SQL, `BEFORE` triggers validate/transform; `AFTER` triggers audit/notify.
- In SQL, `NEW`/`OLD` pseudo-rows expose changed values per row.
- In SQL, statement-level triggers see whole changes without row loops.
- In SQL, cascading triggers recurse dangerously — guard with flags/depth.
- In SQL, prefer constraints/checks over triggers for simple validations.
- In SQL, document triggers visibly; hidden side effects surprise maintainers.
- In SQL, test triggers with multi-row statements, not single inserts only.
