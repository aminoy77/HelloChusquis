# Database backup and restore

- `pg_dump db > backup.sql` snapshots Postgres logically and portably.
- Physical base backups plus WAL archiving enable point-in-time recovery.
- Automate daily fulls plus continuous WAL shipping for sub-minute RPOs.
- Restore drills quarterly prove backups actually boot and serve.
- Encrypt backup files; they contain the same crown jewels as production.
- Test restores on isolated hosts, never against live primaries.
- Retention policies balance compliance minimums against storage costs.
- Replica lag monitoring warns before failovers promote stale standbys.
- Logical dumps migrate versions; physical copies demand version parity.
- Document runbooks with exact commands for 3am operators.
