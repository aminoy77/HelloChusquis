# Go database access (example)

- `database/sql` plus blank-imported drivers keep code portable.
- `sql.Open` validates lazily; `Ping` confirms connectivity eagerly.
- Connection pools (`SetMaxOpenConns`) bound database pressure explicitly.
- Prepared statements (`Prepare`) speed repeats plus stop injection.
- `QueryRow` plus `Scan` map single rows; `Query` iterates multiples.
- `sql.Tx` plus `defer tx.Rollback()` guard multi-statement atomicity.
- `sql.NullString` models nullable columns without pointers.
- Migration tools (golang-migrate) version schemas in CI pipelines.
- sqlc generates type-safe Go from SQL queries at build time.
- Context-aware methods (`QueryContext`) honor cancellations end-to-end.
