# SQL privileges

- `GRANT SELECT ON t TO analyst` scopes access per table and operation.
- REVOKE removes grants deliberately during offboarding and incident response.
- Roles bundle grants; users inherit via membership instead of direct grants.
- Least privilege per service account bounds breach blast radius.
- `GRANT ... WITH GRANT OPTION` delegates carefully — chains obscure auditing.
- Default privileges auto-apply to future tables in owned schemas.
- Row-level security policies filter tenants invisibly at query time.
- Separate migration roles (DDL) from app roles (DML) strictly.
- Audit `information_schema.role_table_grants` quarterly for drift.
- Superuser stays with break-glass accounts, never application logins.
