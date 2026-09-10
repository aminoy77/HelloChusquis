# Full-text search in SQL

- In SQL, `LIKE '%x%'` scans fully; full-text indexes rank matches properly.
- In Postgres, `tsvector` plus `tsquery` with GIN indexes power search.
- In Postgres, `to_tsvector`/`plainto_tsquery` handle stemming and stopwords.
- In Postgres, `ts_rank` orders by relevance, not insertion order.
- In MySQL, `MATCH(col) AGAINST('x' IN NATURAL LANGUAGE MODE)` searches natively.
- In MySQL, `FULLTEXT` needs MyISAM or InnoDB 5.6+ tables.
- In SQLite, FTS5 virtual tables (`USING fts5`) index documents compactly.
- In SQLite, `bm25()` ranks FTS5 results by relevance out of the box.
