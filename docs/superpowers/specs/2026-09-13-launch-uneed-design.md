# HelloChusquis launch design — uneed.best 1/31/2027

Date: 2026-09-13. Status: owner-approved. Single goal: stars + PyPI downloads. OSS, no revenue. Perfect D-day, zero broken.

## 1. Verified context

- Repo: HelloChusquis, local-first AI agent (terminal + web 7272 + REST API + Telegram).
- Real code version: 5.4 (CHANGELOG). `pyproject.toml` said 5.2 → drift to fix in Phase 0.
- Tests: 398/398 green (2026-09-13). README badge said 359 → fix.
- Providers: 54–74 catalog depending on surface; unify the public number.
- Memory: SQLite sessions/summaries/learnings + `MDknowledge/` 1200+ files (~9900 facts).
- Skills today: `core/skills.py` with its own JSON format (`skills/*.json`), approval-gated, bounded shell. `skills-lock.json` + `.agents/skills/` belong to hyperframes (video), not the runtime.
- Subagents: 12 builtins in `agents/`, hard budgets (12 steps / 12k tokens / 180s, 8 concurrent).
- 30s launch video exists: `videos/hellochusquis-launch/renders/video.mp4` (1.3 MB, 1920×1080).

## 2. uneed.best rules (researched 2026-09-13)

- 85k makers, 22k newsletter (weekly top3). Up to 45 launches/day. Daily podium = visibility.
- Permanent listing only with 10+ votes (free launches). Paid launches keep DR75 dofollow backlink always.
- Free queue closed since Aug-2026 (6+ month wait). To secure 1/31/2027 you need Fast-track (~$15) or Skip-the-line (~$30). Phase 0 action: reserve the date NOW.
- 1/31/2027 = Sunday. Low traffic (Tue–Thu ideal). Compensate with pre-launch page + pre-rally. Do not move the date (owner decision: official launch that day).
- Rolling leaderboard: votes always count, including post-launch. 5-day streak = +1 multiplier (x2). Pro = +3 votes + monthly relaunch + private Discord.
- Page needs: logo, title, description, video preview, screenshots, Deal badge (offer → badge + clicks). Buying votes = ban.
- Pre-launch page collects emails → D-day boost.

## 3. Chosen strategy: A + C + scoped skills

- A (stability first): freeze features in Dec. All effort on install, onboarding, web/API, docs, demo.
- C (community): daily streak in Jan, Discord, Reddit/X, prior HN Show, comment replies <1h.
- Universal skills: ONLY new feature. Justification: star magnet for uneed AI/dev voters; passes YAGNI because the SKILL.md ecosystem is the de-facto standard and cost stays low if scoped.
- B (feature-blitz: cloud sync, marketplace, mobile) REJECTED: breaks the perfect-day goal.

## 4. Phases and exit criteria

### Phase 0 — Now/Sep 2026: secure the base
- [ ] Unify version to a single source (pyproject = CHANGELOG = badge).
- [ ] Fix tests badge (359 → real) and public providers/tools number.
- [ ] Clean `pip install hellochusquis` verified in venv (3.10/11/12, mac/linux). `install.sh` tested.
- [ ] `python -m unittest discover tests -q` green + `ruff check .` + `hellochusquis doctor --contracts`.
- [ ] Reserve uneed date (Fast-track/Skip) + publish pre-launch page.
- [ ] Cut uneed preview video from existing render.
- Exit: 100% clean install, date reserved, pre-launch online.

### Phase 1 — Oct: stability
- [ ] Onboarding <2min: `config` / `--quick` → first useful chat.
- [ ] `web`, `api`, `telegram` crash-free; loopback/remote auth intact; viewer/operator/owner roles.
- [ ] Memory + MDknowledge with no regression (35q factual probe).
- [ ] Freeze providers/tools catalog except when broken.
- Exit: zero tracebacks in demo flow, green doctor.

### Phase 2 — Nov: universal skills (closed scope)
Minimal design over existing `core/skills.py`:
- [ ] Discovery: `~/.hellochusquis/skills/*/SKILL.md` + repo `.agents/skills/` + workspace. Order: workspace > home > repo.
- [ ] Parse `name/description` frontmatter with stdlib (no deps). MD body = prompt_template. Folder sidecar files reachable by reference.
- [ ] Reuse `SkillRegistry.list/find`, system-prompt injection, shell execution with existing approval gate. No marketplace, no auto-install, no network.
- [ ] CLI `hellochusquis skills list/run`, 2 demo skills, docs.
- [ ] Tests: valid/invalid parse, blocked path traversal, required approval, injected prompt.
- [ ] Hard cutoff Dec-1: bugfix only after.
- `ponytail:` naive recursive O(n) scan, enough up to ~500 skills; inverted index if needed.

### Phase 3 — Dec: freeze + packaging
- [ ] Zero features. Fixes with regression only.
- [ ] README: banner, demo GIF, 3-step quickstart, real badges, surfaces table, skills section, uneed links.
- [ ] SEO: `hellochusquis.dev`, sitemap, og.
- [ ] Weekly PyPI dry-runs + install matrix + 5-min guide.
- [ ] Uneed Deal badge (OSS offer: free cheat-sheet/template).

### Phase 4 — Jan 2027: community + D-day
- [ ] Daily streak from Jan-1 (posts, votes, others' feedback).
- [ ] Pre-rally: pre-launch emails, X, Reddit (r/selfhosted, r/LocalLLaMA), HN Show days before.
- [ ] D-day: direct vote link, video, web/TUI screenshots, changelog, replies <1h.
- [ ] Post: 2-week momentum (rolling votes count), fixes <24h, top3 newsletter goal.
- Exit: 10+ D-day votes (permanence), top3 podium goal.

## 5. Metrics

- D-day: votes, daily rank, uneed page visits, PyPI installs that week.
- Quality: green tests, 0 critical issues, install→first-chat time.
- Post: GitHub stars, PyPI downloads/month, rolling votes.

## 6. Risks and mitigation

| Risk | Mitigation |
|---|---|
| Slow Sunday | Pre-launch emails + pre-rally + rolling votes |
| Skills scope creep | Dec-1 cutoff, no marketplace |
| Broken install on D-day | Matrix + dry-runs Dec/Jan |
| Version drift | Single source in Phase 0 |
| <10 votes (no permanent listing) | Paid reservation (dofollow secured) + pre-rally |

## 7. Decisions made

- Channel: uneed.best 1/31/2027, fixed date.
- Strategy A+C+scoped skills. B rejected.
- Spec now in English (repo language rule, 2026-09-23).

## 8. Spec self-review (2026-09-13)

- Placeholders: none (uneed prices with ~ for possible change; verified Sep-2026).
- Consistency: sequential phases with no feature overlap after Dec-1. OK.
- Scope: a single feature (skills loader). OK, no breakdown.
- Ambiguity: "public providers/tools number" stays as a Phase 0 task with real counting. OK.
