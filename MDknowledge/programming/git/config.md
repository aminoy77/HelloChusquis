# Git config

- In Git, `git config user.name/email` identifies authorship per repo or `--global`.
- In Git, `git config --list --show-origin` audits effective settings and their files.
- In Git, `git config core.editor` picks the commit-message editor deterministically.
- In Git, `git config pull.rebase true` makes `git pull` replay instead of merging.
- In Git, `git config init.defaultBranch main` names the initial branch on `git init`.
- In Git, `git config --global alias.co checkout` shortens daily commands safely.
- In Git, credential helpers (`manager`, `store`, `cache`) persist HTTPS auth per platform.
- In Git, `includeIf gitdir:` scopes configs to work versus personal directories.
- In Git, `commit.gpgsign true` signs every commit once keys are configured.
- In Git, `.gitattributes` (`*.png binary`, `*.md text`) tunes diffing and line endings per path.
