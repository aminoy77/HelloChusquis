# ARIA accessibility

- ARIA supplements HTML semantics; native elements (`<button>`) come first always.
- Roles (`role='dialog'`) declare widget types assistive tech announces.
- States (`aria-expanded`, `aria-selected`) must update synchronously with UI.
- `aria-label` names icon buttons lacking visible text for readers.
- `aria-live` regions announce dynamic updates (errors, toasts) politely.
- `aria-hidden='true'` hides decorative duplicates from screen readers.
- Focus management (trap in modals, restore on close) completes keyboard flows.
- Landmarks (`banner`, `main`, `navigation`) enable reader quick-navigation.
- Color alone never conveys meaning; pair with text or icons.
- Test with real screen readers plus keyboard-only passes regularly.
