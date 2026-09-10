# Frontend state (example)

- Local state (`useState`) suits component-private UI toggles.
- Lifted state shares via props one level up, not global stores.
- Context API broadcasts themes/locales without prop drilling.
- External stores (Zustand, Redux) centralize cross-cutting domain state.
- Server state (React Query) caches fetches separately from UI state.
- URL state (query params) shares deep links plus back-button support.
- Form state libraries tame validation/dirtiness at scale.
- State machines (XState) kill impossible UI states declaratively.
- Normalize relational data (entities keyed by id) avoiding duplication.
- Derived state computes (selectors) instead of syncing duplicates.
