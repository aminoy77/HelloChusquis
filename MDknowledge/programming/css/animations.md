# CSS animations

- In CSS, `transition: transform .2s ease` animates property changes on state flips.
- In CSS, `@keyframes` plus `animation: name 1s infinite` loops declarative motion.
- In CSS, `transform: translate/scale/rotate` animates on the compositor for smooth 60fps.
- In CSS, prefer `opacity`/`transform` over layout properties (`width`, `top`) for performance.
- In CSS, `animation-fill-mode: forwards` holds the final keyframe after finishing.
- In CSS, `prefers-reduced-motion: reduce` media queries must disable non-essential motion.
- In CSS, `transition-delay` staggers siblings for cascading entrance effects.
- In CSS, `cubic-bezier()` curves tune easing beyond named keywords like `ease-out`.
- In CSS, `will-change: transform` hints the browser but overuse wastes memory.
- In CSS, `animation-play-state: paused` freezes motion for toggles and debugging.
