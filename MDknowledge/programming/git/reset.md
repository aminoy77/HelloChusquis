# Git reset and restore

- In Git, `git restore <file>` discards unstaged changes; `--staged` unstages instead.
- In Git, `git reset --soft HEAD~1` undoes a commit keeping work staged for re-commit.
- In Git, `git reset --mixed` (default) unstages while preserving working-tree edits.
- In Git, `git reset --hard` destroys uncommitted work irreversibly — verify with `git stash` first.
- In Git, `git revert <sha>` undoes via a new commit, safe for shared branches.
- In Git, `git checkout <sha> -- <file>` resurrects one file's old version selectively.
- In Git, `git clean -nd` previews untracked deletions before `git clean -f` executes.
- In Git, `git reflog` recovers commits orphaned by resets for about 90 days.
- In Git, `ORIG_HEAD` points at the pre-reset commit for quick `git reset ORIG_HEAD` escapes.
- In Git, prefer revert on pushed history and reserve reset for private branches.
