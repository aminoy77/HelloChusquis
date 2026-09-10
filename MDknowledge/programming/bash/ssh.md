# Bash ssh

- In Bash, `ssh user@host` opens encrypted remote shells over port 22.
- In Bash, `ssh-keygen -t ed25519` creates modern keypairs; never share private keys.
- In Bash, `ssh-copy-id user@host` installs public keys for passwordless login.
- In Bash, `~/.ssh/config` aliases hosts with users, ports, and identity files.
- In Bash, `scp file user@host:path` copies files; `rsync -avz` syncs trees efficiently.
- In Bash, `ssh -L 8080:localhost:80 host` forwards remote services to local ports.
- In Bash, `ssh -J jump final` hops through bastion hosts transparently.
- In Bash, `StrictHostKeyChecking` guards against impostor servers on first connect.
- In Bash, `ssh-agent` plus `ssh-add` cache decrypted keys for a session.
- In Bash, `mosh` roams across networks where plain ssh sessions would freeze.
