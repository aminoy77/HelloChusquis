# rsync backups

- `rsync -avz src/ dst/` syncs with archive mode, verbosity, and compression.
- Trailing slashes decide contents-vs-directory copies — get them right deliberately.
- `--delete` mirrors deletions; omit it (or `--backup`) against accidental wipes.
- `--exclude='.git/'` skips bulky or sensitive subtrees from transfers.
- `-n/--dry-run` previews destructive syncs safely before committing.
- SSH transport (`-e 'ssh -p 2222'`) secures remote copies transparently.
- `--link-dest` hardlinks unchanged files for space-efficient snapshots.
- `--bwlimit` throttles business-hours syncs off production links.
- `--partial --progress` resumes interrupted giants instead of restarting.
- Verify with checksums (`-c`) periodically; timestamps alone can lie.
