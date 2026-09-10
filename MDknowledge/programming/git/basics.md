# Git basics

- In Git, `git init` starts a repository and `git clone <url>` copies a remote one locally.
- In Git, `git status` shows staged, modified, and untracked files before every commit.
- In Git, the workflow is edit, `git add <files>`, then `git commit -m "message"` to snapshot.
- In Git, `git diff` shows unstaged changes and `git diff --staged` shows what the next commit contains.
- In Git, `git log --oneline -10` summarizes recent history compactly.
- In Git, `git show <commit>` displays one commit's diff and metadata.
- In Git, `.gitignore` excludes generated files; committed files must be untracked first with `git rm --cached`.
- In Git, `git mv` and `git rm` stage renames and deletions so history stays coherent.
- In Git, `git stash` shelves uncommitted work and `git stash pop` restores it.
- In Git, `git checkout -- <file>` (or `git restore <file>`) discards unstaged changes permanently.
- In Git, `git reset --soft HEAD~1` undoes the last commit but keeps the changes staged.
- In Git, `git commit --amend` folds fixes into the previous commit; never amend pushed shared history.
- In Git, `git remote -v` lists remotes; `git push origin <branch>` publishes a branch.
- In Git, `git pull` fetches plus merges; `git fetch` only downloads, letting you inspect first.
- In Git, `git config user.name/user.email` identifies authorship per repository or globally.
- In Git, commit messages use an imperative short subject ("Add login") plus context in the body when needed.
- In Git, `HEAD` names the current commit; `HEAD~1` is its parent.
- In Git, `git blame <file>` attributes each line to its last-modifying commit.
