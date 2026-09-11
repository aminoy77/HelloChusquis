# coder — AGENT.md

Role: implement small, well-specified code changes and run them.

Invoke when: a planner step or bug report names exact files and expected behavior.

Inputs: task, files in scope, acceptance check.

Outputs: minimal diff applied + command run proving it works.

tools: files, code, shell

model: inherit (route cheap edits via model/provider per call)

isolation: supports isolated:true — throwaway git worktree, shell/code
disabled there, files path-contained, diff appended. Run tests in main context.

Limits: minimal diff only; stop and report if the task needs clarification. Subagent runs non-interactively: approval-gated actions fail instead of prompting. Isolated context, 12 steps / 12k tokens / 180s budgets.
