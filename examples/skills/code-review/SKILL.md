---
name: code-review
description: Review a diff or file with strict, actionable findings.
---

# Code review

Be strict, specific, and brief.

1. Read the full diff first; never comment on lines you haven't seen.
2. Report only real defects: wrong behavior, crashes, data loss, security holes, broken contracts.
3. Skip style nits unless they hide a bug.
4. Every finding needs: file + line, what's wrong, why it matters, a concrete fix.
5. Check: error paths, empty inputs, off-by-one, leaked secrets, unhandled rejections.
6. If the change is safe, say so in one line and stop.

Output: findings ordered by severity, then a one-line verdict (approve / needs work).
