# Git revert and cherry-pick

- In Git, `git revert <sha>` creates an inverse commit, preserving full history.
- In Git, `git revert --no-commit` stages multiple reverts for one combined undo commit.
- In Git, reverting a merge needs `-m 1` to select the mainline parent explicitly.
- In Git, `git cherry-pick <sha>` replays single commits onto the current branch.
- In Git, `cherry-pick -x` records the source commit id in the message for traceability.
- In Git, `cherry-pick -n` stages without committing to batch several picks.
- In Git, `--continue`/`--skip`/`--abort` steer conflicted cherry-picks like rebases.
- In Git, conflicts during picks resolve exactly like merge conflicts (markers, add, continue).
- In Git, prefer merges for whole branches and picks for surgical single-commit backports.
- In Git, `git revert` of a revert re-applies: double negatives restore original changes.
