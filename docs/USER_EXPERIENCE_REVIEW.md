# User experience review

**Date:** August 20, 2026  
**Scope:** First CLI run with no prior configuration, offline diagnostics, and recovery toward initial setup.

## Walkthrough

Ran the flows a person would follow after installing the tool to check its state before connecting a provider: `hellochusquis --help`, `hellochusquis doctor --contracts`, `hellochusquis doctor`, `hellochusquis config --show`, and the intuitive `hellochusquis status` command.

The base walkthrough is solid. Help lists the main actions, contract diagnostics work offline, and unconfigured paths answer with a concrete instruction to run `hellochusquis setup`. This keeps an incomplete install from failing with internal traces or ambiguous assistance.

## Verified friction

| Priority | Observed finding | Impact on the user | Committed fix |
|---|---|---|---|
| High | `hellochusquis status` does not exist and answers as an unknown command. | The most natural readiness check fails, although `doctor` covers part of it. | Add `status` as a non-interactive summary of configuration, readiness, and optional contracts. |
| High | The CLI API binds to `0.0.0.0` by default. | A person can accidentally publish an authenticated API on their network on first run. | Change the default to `127.0.0.1`; keep `--host 0.0.0.0` as an explicit choice. |
| Medium | Config diagnostics and contracts are separate commands. | You must remember which check fits each problem type. | The new status view shows local readiness at a glance and offers offline contracts on demand. |

## Acceptance criteria

Fixes must keep existing diagnostics, never leak secrets or local paths, and preserve the explicit option to expose the API when the operator needs it. They must include CLI regression tests and the project's full suite.
