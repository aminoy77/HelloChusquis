# XSS prevention

- Cross-site scripting injects attacker JavaScript into victim pages.
- Escape output by context: HTML, attribute, JS, URL, and CSS rules differ.
- Framework auto-escaping (React, Vue templates) beats manual escaping discipline.
- `innerHTML` with user data is the classic sink; prefer `textContent` or sanitizers.
- Content Security Policy headers neuter inline scripts even after injection.
- HttpOnly cookies keep session tokens from stolen script reach.
- Stored XSS persists in databases striking every viewer; reflected hits single victims.
- DOM XSS sinks (`location.hash` into sinks) bypass server-side filters entirely.
- DOMPurify sanitizes rich HTML when markup must survive user input.
- Test with polyglot payloads plus automated scanners in CI.
