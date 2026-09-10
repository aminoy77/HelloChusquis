# Git stash

- In Git, `git stash push -m 'wip'` shelves work with a findable message.
- In Git, `git stash -u` includes untracked files; default stashes tracked changes only.
- In Git, `git stash list` enumerates stashes newest-first with their messages.
- In Git, `git stash pop` restores and drops; `apply` restores while keeping the entry.
- In Git, `git stash show -p stash@{1}` previews older stashes before restoring.
- In Git, `git stash branch <name>` resurrects conflicted stashes onto fresh branches.
- In Git, `git stash drop` discards entries deliberately after verifying restores.
- In Git, partial stashes (`git stash push -p`) shelve selected hunks only.
- In Git, stashes are local-only; push a WIP branch instead to share work.
- In Git, `git stash clear` wipes all entries irreversibly — verify first.
