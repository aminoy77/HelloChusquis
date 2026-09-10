# Python pandas

- pandas DataFrames label rows and columns for tabular analysis.
- `read_csv/read_parquet` ingest; `to_csv/to_parquet` persist round-trips.
- `df.head/info/describe` profile new datasets in three commands.
- Boolean masks (`df[df.age > 30]`) filter rows expressively.
- `groupby(...).agg(...)` splits, applies, and combines summaries powerfully.
- `merge` joins on keys (inner/left/outer); `concat` stacks vertically.
- `fillna/dropna` handle missing data explicitly before modeling.
- `df.apply` row-wise Python is slow; prefer vectorized columns.
- Datetime accessors (`.dt.year`) plus categoricals compress memory hugely.
- `df.query` strings read cleaner than chained boolean masks.
