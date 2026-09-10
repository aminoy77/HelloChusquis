# Bash permissions

- In Bash, `ls -l` leading flags (`rwxr-xr--`) encode owner/group/other permissions.
- In Bash, `chmod 644 file` sets owner read-write with world read-only for data.
- In Bash, `chmod 755 script.sh` adds execute bits for runnable scripts and directories.
- In Bash, `chmod 600 secrets` restricts sensitive files to the owner only.
- In Bash, `chmod -R` recurses trees; pair with `find -type` guards to spare files or dirs.
- In Bash, `chown user:group file` transfers ownership where privileges allow.
- In Bash, `umask 027` defaults new files to owner-full, group-read, other-none.
- In Bash, setuid/setgid/sticky bits (`4755`, `2755`, `1777`) need deliberate justification.
- In Bash, `chmod +x` adds execute without disturbing existing read/write bits.
- In Bash, directories need execute bits for traversal, not just read for listing.
