# Git log and history

- In Git, `git log --oneline --graph --decorate -20` visualizes recent branching compactly.
- In Git, `git log -p <file>` shows patch history for one path across renames with `--follow`.
- In Git, `git log --since='2 weeks ago'` and `--author=` filter history slices quickly.
- In Git, `git log -S 'string'` (pickaxe) finds commits adding or removing exact text.
- In Git, `git log -G 'regex'` extends pickaxe to pattern matches in diffs.
- In Git, `git show <sha> --stat` summarizes one commit before diving into full diffs.
- In Git, `git shortlog -sn` ranks contributors by commit count for release notes.
- In Git, `git log --format='%h %ad %s'` customizes columns with date and subject.
- In Git, `git blame -L 10,20 <file>` attributes line ranges for focused archaeology.
- In Git, `git log main..feature` previews exactly what a merge would introduce.
