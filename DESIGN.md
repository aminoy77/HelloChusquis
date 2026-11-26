# HelloChusquis design system

## Direction

HelloChusquis uses a fixed near-white engineering-plate visual world. It is calm, precise, and work-oriented: the logo is the sole brand device, while type, hairlines, and the periwinkle action color make hierarchy legible without terminal effects or decorative containers.

## Color

- Surface: `#F7F7F5`
- Panel: `#FFFFFF`
- Secondary surface: `#F1F1EE`
- Ink: `#1B1D1F`
- Secondary text: `#5E6266`
- Hairline: `#D8DAD6`
- Soft hairline: `#E7E8E4`
- Primary action and seal: `#5D67E8`
- Hover action: `#4B55CC`
- Success: `#287A55`
- Error: `#B44343`
- Supporting blue: `#456A9D`

Body text uses ink on the near-white field. Muted text uses `#5E6266`, preserving a 4.5:1-or-better reading contrast.

## Type

- Interface: system UI stack
- Code and data: SF Mono / Menlo / Consolas / monospace fallback
- Display: system UI with tight negative tracking only for large landing headlines

No alternate fonts or type choices are exposed in the interface.

## Layout

The landing viewport is a split engineering plate: direct product copy and install actions on the left, with a measured local-session readout on the right. Long-form sections use flat hairline grids rather than repeated cards. The application uses a compact header, rail-like provider sidebar, flat message canvas, and fixed composer.

Compact widths stack the landing plate, hide secondary navigation, and use a single-column section grid. Modal surfaces remain constrained to the viewport.

## Components

- Controls use flat surfaces, 7-10px radii, hairline borders, and restrained hover states.
- Primary actions use periwinkle with white text.
- Panels and dialogs use white surfaces and thin borders without blur or shadows.
- The marketplace keeps its catalog grid and install/uninstall states, with flat cards and action buttons.
- Appearance is fixed and the appearance panel explains the fixed visual status.

## Motion

Motion is limited to short landing reveals and control state transitions. Reduced-motion preferences remove animation and force immediate transitions.

## Accessibility

Keep a visible focus ring, semantic landmarks, keyboard-operable controls, meaningful labels, and no state communicated by color alone. No text-only configuration choice is needed to interpret the interface.
