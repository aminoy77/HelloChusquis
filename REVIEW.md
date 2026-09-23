# Critical product review — HelloChusquis

**Status:** technical review after audit and local user walkthroughs.  
**Criteria:** operational reliability, isolation between users, security, and product coherence.

> The project has strong ambition —an agent with terminal, web, API, and multiple providers— but before this intervention it mistook catalog breadth for maturity. An integration list does not equal a reliable product if first boot can block a server, if the web UI is open by default, or if two users can share context.

| Area | Critical finding | Impact | Product decision |
|---|---|---:|---|
| Boot | The API and web launched an interactive assistant at import time when configuration was missing. | High | Turn the failure into recoverable readiness state, keeping the process alive. |
| Configuration | The agent received a configuration but re-read it from disk; also, a keyless local provider could be discarded. | High | Use the received configuration and accept valid local configurations. |
| Web security | The web exposed powerful actions with authentication disabled by default. | Critical | Mandatory authentication by default, with an explicit exception only for isolated development. |
| Concurrency | The web temporarily replaced the global tool dispatcher to log calls. | High | Replace it with per-request callbacks. |
| Privacy | The server reused a single conversation history for all HTTP clients. | Critical | Introduce isolated, bounded agent sessions with LRU. |
| Operations | No clear recovery paths after running `setup`; inspection commands could open an assistant. | Medium | Add live reload and make diagnostic commands non-interactive. |
| Coherence | The announced version, the CLI, and the docs did not share a single source of truth. | Medium | Centralize the version and fix docs/help. |
| Quality | Initial coverage was 14% and validated neither web, API, nor a real provider. | High | Add regressions and authenticated HTTP walkthroughs with a stubbed local provider. |

The conclusion is deliberately harsh: **it was indefensible to present the system as a production-grade agent or comparable to a mature agent while isolation, non-interactive boot, and default authentication were failing**. Those gaps are addressed on this branch; the remaining work from this review is explicit hot recovery and verifiable version coherence.

## Improvements implemented next

| Feature | Expected outcome | Verification |
|---|---|---|
| Live runtime reload | After running configuration, an authorized operator can rebuild agents without restarting the process. | Protected route plus success/error test. |
| Session observability | Status reports in-memory active sessions without leaking histories. | Status field plus isolated-session test. |
| Single version source | CLI, API, and web return the same published version. | Unit tests and command checks. |
| Updated usage contract | Help and guide reflect the real port, default authentication, and recovery. | README review and `--help` output. |

## Limits that remain real

The session cap protects memory but does not replace multiuser authentication, per-client process isolation, permission auditing, or a job queue. The hundred-plus declared integrations require independent contract tests before promising production support. A language model does not make a command safe either: tool policy needs continuous adversarial testing and approval controls for destructive or external actions.

## Maturity update — second iteration

The second iteration turns one of the first review's worst limits —autonomous execution of externally-effective actions— into a verifiable flow of **proposal, explicit approval, and single execution**. On HTTP surfaces, shell and code tools, file mutation, browser submissions, MCP calls, and external actions with mutable verbs no longer execute immediately. The agent creates a session-local, expiring request with an opaque identifier; the authenticated user must approve or reject it.

| Developed capability | Implemented guarantee | Validation evidence |
|---|---|---|
| Human approvals | High-impact actions require an explicit decision in API and web. | Unit tests for classification, denial, and approval. |
| Replay protection | Approval moves to executing state before dispatching the tool; a second attempt fails. | HTTP walkthrough: single approval followed by `409` on repeat. |
| Approval isolation | Requests belong to a single HTTP session's agent. | Adversarial walkthrough: a second session sees an empty list and gets `404` when deciding. |
| Expiry and bounds | Pending requests expire after five minutes and the queue is bounded. | Controlled-clock tests plus equivalent-request dedup. |
| Minimum secret | The public approval view redacts keys, tokens, cookies, passwords, and secrets. | Recursive redaction regression test. |
| Structured streaming | The agent emits an approval SSE event with the exact identifier and reason. | Walkthrough with stubbed local provider and client confirmation card. |
| HTTP compatibility | A file approval keeps a server from blocking on a terminal confirmation. | Controlled-write walkthrough: nonexistent before approval, created after. |
| Contract diagnostics | `hellochusquis doctor --contracts` imports and checks the entry point of the 48 agent-exposed integrations, with no network or credentials. | Local run: 48/48 structural contracts valid. |

> **Unvarnished verdict:** the project made a real leap from "agent that executes" to "agent that asks authorization before changing things". That was essential. Still, this improvement alone does not make the product equivalent to Hermes Agent nor authorize claiming such equivalence.

## Outstanding gaps for serious parity with a top-tier agent

| Remaining gap | Why it still matters | Next investment needed |
|---|---|---|
| Process isolation | Sessions separate history and approvals but share process, network, and local storage. | Ephemeral task-isolated executors with CPU, memory, file, and network limits. |
| Multiuser identity | A single API token identifies the deployment, not separate people or roles. | User authentication, roles, session owners, and per-tool authorization. |
| Durable audit | Approvals live in memory and are lost on restart. | Persistent, immutable, queryable record of decisions, redacted arguments, and results. |
| Real integrations | Contract verification guarantees import and `run`, not valid credentials or per-provider behavior. | Per-provider contract suites with sandbox/mock environments and API-version tests. |
| Semantic policy | Tool-and-verb classification is conservative but does not understand every business effect. | Per-action risk schemas, monetary limits, and stepped approvals. |
| Execution recovery | After approval the action runs and shows its result; the model does not automatically resume the plan with that result. | Task orchestration with durable states, resumption, and compensation. |

Closing validation for this iteration includes **89 unit tests**, full build, static analysis of modified files, high-severity security review, HTTP tests with stubbed local provider, replay test, and cross-session adversarial test. This evidence supports the described capabilities; it must not be extrapolated into a guarantee over untested external APIs.

## Recommended priority

The rational path to a genuinely robust agent is not adding more integration logos. It is building, in this order: **multiuser identity and roles**, **persistent decision auditing**, **per-task isolated execution**, and **per-provider contract tests**. Everything else is cosmetic until those four layers exist.
