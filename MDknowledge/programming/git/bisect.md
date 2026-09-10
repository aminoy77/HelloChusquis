# Git bisect

- In Git, `git bisect start` plus good/bad marks binary-search regressions.
- In Git, `git bisect run pytest test_x` automates the whole bisection.
- In Git, `git bisect reset` returns to the original branch afterward.
- In Git, `git bisect skip` routes around untestable middle commits.
- In Git, `git bisect visualize` graphs remaining suspects for intuition.
- In Git, scriptable reproductions (exit codes) beat manual testing per step.
- In Git, bisect needs linearizable history; merge-heavy trees confuse it.
- In Git, `git bisect log` documents findings for the eventual fix commit.
