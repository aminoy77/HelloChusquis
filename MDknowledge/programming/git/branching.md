# Git branching and merging

- In Git, `git branch <name>` creates a branch and `git switch <name>` (or `checkout`) moves onto it.
- In Git, `git switch -c <name>` creates and switches in one step for feature work.
- In Git, `git merge <branch>` joins another branch into the current one, creating a merge commit on conflicts or `--no-ff`.
- In Git, `git rebase main` replays the current branch onto main for linear history; never rebase pushed shared branches.
- In Git, `git merge --abort` and `git rebase --abort` bail out of conflicted operations safely.
- In Git, conflict markers `<<<<<<<`, `=======`, `>>>>>>>` delimit competing versions; edit, `git add`, then continue.
- In Git, `git mergetool` launches a visual resolver when manual marker editing gets confusing.
- In Git, `git branch -d <name>` deletes merged branches; `-D` forces deletion of unmerged work.
- In Git, `git push -u origin <branch>` sets upstream tracking so later `git push`/`pull` need no arguments.
- In Git, `git fetch origin` plus `git log main..origin/main` previews incoming changes before merging.
- In Git, `git cherry-pick <commit>` replays one commit onto the current branch for surgical backports.
- In Git, `git revert <commit>` undoes via a new commit, the safe choice for shared history.
- In Git, `git stash -u` includes untracked files; `git stash list` and `git stash apply` manage multiple stashes.
- In Git, `git worktree add ../hotfix` checks out a second branch beside the main working copy.
- In Git, `git reflog` recovers seemingly lost commits for about 90 days after resets and rebases.
- In Git, `git tag v1.2.0` marks releases; `git push origin v1.2.0` publishes the tag.
- In Git, short-lived feature branches merged via pull request keep main releasable.
- In Git, `git rebase -i HEAD~3` rewrites recent local commits (squash, reword) before opening a PR.
