# Backup security

- 3-2-1 rule: three copies, two media types, one offsite/offline against ransomware.
- Encrypt backups; unencrypted archives are breach-equivalent data stores.
- Test restores quarterly — untested backups are Schrödinger's safety net.
- Immutable (WORM) snapshots survive attackers wielding stolen admin creds.
- Separate backup credentials from production admin paths entirely.
- RPO sets acceptable data loss windows; RTO sets downtime budgets — design to both.
- Versioned backups defeat silent corruption discovered months later.
- Document restore runbooks with exact commands, not tribal knowledge.
- Monitor backup job success like production SLIs, with paging on failure.
- Retain per legal minimums, then destroy — hoarding expands breach blast radius.
