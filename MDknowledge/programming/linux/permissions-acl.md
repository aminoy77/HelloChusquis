# Linux ACLs and sudo

- POSIX bits cover owner/group/other; ACLs (`setfacl`) grant per-user exceptions.
- `getfacl file` reveals effective rights beyond `ls -l` simplifications.
- `setfacl -m u:ana:rw file` shares precisely without group sprawl.
- `sudo command` elevates per policy in `/etc/sudoers` (edit via `visudo`).
- `sudo -u svc cmd` runs as service users for permission-faithful debugging.
- `sudo -i` simulates full root logins versus `sudo -s` shell upgrades.
- `timestamp_timeout` bounds credential caching between password prompts.
- NOPASSWD suits automation accounts, never interactive human users.
- `/var/log/auth.log` (or secure) audits every elevation attempt centrally.
- Principle of least privilege: grant commands, not shells, where possible.
