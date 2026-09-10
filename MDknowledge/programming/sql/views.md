# SQL views

- In SQL, `CREATE VIEW v AS SELECT ...` names reusable queries behind a table-like facade.
- In SQL, views encapsulate reporting logic so schema refactors touch one place.
- In SQL, simple single-table views accept INSERT/UPDATE where the database permits it.
- In SQL, materialized views precompute results and refresh on schedule or demand.
- In SQL, `CREATE OR REPLACE VIEW` updates definitions without dropping dependents.
- In SQL, views restrict columns/rows per role as a lightweight access-control layer.
- In SQL, `WITH CHECK OPTION` blocks writes through views that would escape their filter.
- In SQL, nested views hide costs; profile the expanded query, not the name.
- In SQL, `DROP VIEW IF EXISTS` makes migration scripts rerunnable.
- In SQL, version reporting views (`v2`) during transitions instead of breaking consumers.
