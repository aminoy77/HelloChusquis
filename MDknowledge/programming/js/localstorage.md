# Web storage

- `localStorage` persists string key-values across sessions per origin (~5MB).
- `sessionStorage` clears when its tab closes, unlike localStorage.
- Both store strings only; `JSON.stringify/parse` round-trips objects.
- Quota errors need try/catch fallbacks to in-memory maps.
- Storage events sync cross-tab updates for multi-tab apps.
- Never store secrets/tokens in web storage — XSS reads it freely.
- IndexedDB handles structured offline datasets beyond 5MB budgets.
- Cookies (httpOnly, Secure) carry session tokens storage cannot protect.
- Cache API plus service workers serve offline-first experiences.
- Version stored schemas; migrations prevent stale-shape crashes.
