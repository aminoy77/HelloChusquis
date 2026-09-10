# Linux users and groups

- `id`, `whoami`, and `groups` report identity and memberships instantly.
- `useradd -m -s /bin/bash name` creates login users with home directories.
- `usermod -aG sudo name` grants admin via group membership (append, never replace).
- `passwd -l user` locks logins while preserving files for leavers.
- `userdel -r` removes accounts plus home directories on offboarding.
- `/etc/passwd` maps users publicly; `/etc/shadow` guards hashes root-only.
- `sudo visudo` edits privilege rules with syntax checking against lockouts.
- `su - user` adopts full login environments for debugging as others.
- Service accounts get `/usr/sbin/nologin` shells plus no passwords.
- Review `lastlog` and dormant accounts quarterly for hygiene.
