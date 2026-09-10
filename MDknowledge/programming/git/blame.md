# Git blame

- In Git, `git blame <file>` attributes each line to its last-modifying commit.
- In Git, `git blame -L 10,20` scopes attribution to the interesting range.
- In Git, `git blame -w` ignores whitespace-only changes to find real authors.
- In Git, `git blame -M` detects moved lines across the same file.
- In Git, `git blame -C` additionally traces lines copied from other files.
- In Git, `--since` bounds blame walks for faster results on huge files.
- In Git, porcelain format (`--porcelain`) feeds blame data to scripts reliably.
- In Git, `git log -L` shows a line range's full evolution, not just its last touch.
- In Git, blame answers 'who last touched', not 'who is responsible' — read the commit message.
- In Git, `.git-blame-ignore-revs` skips formatting commits to keep attribution meaningful.
