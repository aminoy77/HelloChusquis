# SQL CREATE TABLE

- `CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)` defines storage explicitly.
- Choose narrowest correct types: INTEGER over TEXT numerics, DATE over strings.
- `PRIMARY KEY` implies UNIQUE plus NOT NULL with backing index automatically.
- `FOREIGN KEY (uid) REFERENCES users(id)` declares relationships enforceably.
- `DEFAULT now()` timestamps rows without application code.
- `CHECK (price >= 0)` encodes domain rules the optimizer can exploit.
- `CREATE TABLE IF NOT EXISTS` makes migration scripts rerunnable safely.
- Name constraints (`CONSTRAINT uq_email UNIQUE(email)`) for readable errors.
- Comments (`COMMENT ON`) document schema intent where teams forget otherwise.
- Review generated DDL (`pg_dump --schema-only`) before promoting migrations.
