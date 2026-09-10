# SQL constraints

- In SQL, `PRIMARY KEY` uniquely identifies rows and implies NOT NULL.
- In SQL, `FOREIGN KEY ... REFERENCES` declares relationships enforced at write time.
- In SQL, `ON DELETE CASCADE` removes children with parents; default restrict blocks instead.
- In SQL, `UNIQUE` forbids duplicate values across the constrained columns.
- In SQL, `NOT NULL` rejects missing values where absence is invalid.
- In SQL, `CHECK (price >= 0)` encodes domain rules the optimizer can also exploit.
- In SQL, `DEFAULT now()` fills timestamps without application code.
- In SQL, constraint violations raise errors: validate user input before hitting the database.
- In SQL, deferrable constraints check at COMMIT for temporarily inconsistent intermediates.
- In SQL, name constraints explicitly (`CONSTRAINT uq_email`) for readable error messages.
