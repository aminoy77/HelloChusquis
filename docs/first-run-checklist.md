# First-run checklist — 60 seconds, no terminal skills needed

Goal: prove a non-technical visitor can go from zero to an answered question.
Automated smoke passed 2026-09-23 (health ok, 4/4 providers ready, landing 200,
chat 200; 3B answers correctly, 1B is too small for tool calls).

## The 60-second script (give this to your tester)

1. Open `http://localhost:7272` (after running `hellochusquis web`).
2. Click **Launch app** on the landing.
3. Send: `What can you do?`
4. Expected: a streamed reply listing tools, visible tool calls, no errors.
5. Send: `What is the capital of Egypt?`
6. Expected: `Cairo`, one sentence, no approval popup (read-only question).

## Pass criteria

- [ ] Landing loads with no console errors.
- [ ] Chat streams tokens (not one frozen block, no 60s hang).
- [ ] High-impact demo: send `list my home directory files` → an approval card
      appears and nothing executes until approved.
- [ ] Reload keeps working; `/health/ready` returns ok.

## If it fails

- Blank page → check terminal for `Port 7272 unavailable` (it auto-picks another; read the log line).
- `Agent runtime is not ready` → run `hellochusquis config` (or `--quick`) first.
- Slow first answer on local models → normal: the model loads into memory once (~1-2 min on CPU), then it's fast.
