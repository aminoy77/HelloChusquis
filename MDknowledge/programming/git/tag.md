# Git tags

- In Git, `git tag v1.2.0` marks releases with lightweight pointers.
- In Git, annotated tags (`-a -m`) store tagger, date, and message for releases.
- In Git, `git push origin v1.2.0` publishes one tag; `--tags` publishes all.
- In Git, `git tag -l 'v1.*'` lists version families for changelogs.
- In Git, `git describe` names the current commit relative to the nearest tag.
- In Git, `git checkout v1.2.0` inspects releases detached; branch before editing.
- In Git, `git tag -d` plus `push --delete origin` retracts mistaken tags deliberately.
- In Git, GPG-signed tags (`-s`) authenticate release artifacts for consumers.
- In Git, semantic versions (`MAJOR.MINOR.PATCH`) communicate breaking versus additive change.
- In Git, tag release commits, not moving branch tips, for reproducible builds.
