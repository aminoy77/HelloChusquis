# CSRF prevention

- CSRF tricks authenticated browsers into firing unwanted state-changing requests.
- SameSite=Lax cookies block most cross-site forged GETs/POSTs by default now.
- Anti-CSRF tokens (per-session secrets) validate intent on mutations.
- Custom headers (`X-Requested-With`) plus CORS checks stop simple forged forms.
- GET endpoints must never mutate state; reserve writes for POST/PUT/DELETE.
- Re-authenticate (password step-up) before email changes and payouts.
- Check `Origin`/`Referer` server-side as defense-in-depth, not sole control.
- Subdomain takeovers bypass naive origin allow-lists — enumerate exactly.
- Logout CSRF annoys more than harms, but fix it with the same tokens.
- Test with a malicious page auto-submitting to staging forms.
