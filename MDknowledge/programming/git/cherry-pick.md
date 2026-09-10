# Git cherry-pick practice

- In Git, pick release fixes from main with `git cherry-pick <sha>` on the release branch.
- In Git, `-x` appends the origin line so reviewers trace backports to main.
- In Git, conflicting picks pause for marker resolution before `--continue`.
- In Git, `git cherry-pick A..B` replays ranges excluding A itself.
- In Git, empty picks (already applied) skip with `--skip` after inspection.
- In Git, `git log --cherry` highlights diverged duplicates across branches.
- In Git, `git patch-id` detects content-identical commits despite different SHAs.
- In Git, backport tests alongside fixes so release branches prove the repair.
- In Git, announce picks in PR descriptions to avoid double-landing the same change.
- In Git, prefer fast-forward merges over long pick chains for whole features.
