# CSS basics

- In CSS, `selector { property: value; }` rules target elements matched by the selector.
- In CSS, specificity order is inline styles, then `#id`, then `.class`/attributes, then element names.
- In CSS, the box model is content plus padding plus border plus margin, sized outward by default.
- In CSS, `box-sizing: border-box` includes padding and border in the declared width, simplifying layouts.
- In CSS, `display: flex` with `justify-content` (main axis) and `align-items` (cross axis) builds one-dimensional layouts.
- In CSS, `display: grid` with `grid-template-columns: 1fr 2fr` builds two-dimensional layouts with fractional units.
- In CSS, `margin` separates elements externally while `padding` spaces content inside the border.
- In CSS, `margin: 0 auto` centers fixed-width block elements horizontally.
- In CSS, `position: relative` offsets from normal flow; `absolute` positions against the nearest positioned ancestor.
- In CSS, `position: sticky` glues headers in view within their scroll container.
- In CSS, `z-index` orders positioned siblings; unpositioned elements ignore it.
- In CSS, `rem` units scale with the root font size, making whole-layout scaling trivial.
- In CSS, media queries like `@media (max-width: 700px)` adapt layouts to narrow screens.
- In CSS, custom properties (`--accent: red;` used as `var(--accent)`) theme consistently with one change point.
- In CSS, `:hover`, `:focus-visible`, and `:nth-child()` pseudo-classes style states without extra markup.
- In CSS, `transition: all 0.2s` animates property changes; prefer `transform`/`opacity` for smooth 60fps motion.
- In CSS, `* { margin: 0; padding: 0; box-sizing: border-box; }` is a common minimal reset starting point.
- In CSS, prefer classes over ids for styling so rules stay reusable and low-specificity.
