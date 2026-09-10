# CSS positioning

- In CSS, `static` is default flow; offsets apply only to positioned elements.
- In CSS, `relative` nudges from normal position while preserving its flow slot.
- In CSS, `absolute` anchors to the nearest positioned ancestor, else the viewport root.
- In CSS, `fixed` pins to the viewport through scrolling; mind mobile zoom quirks.
- In CSS, `sticky` toggles between relative and fixed within its scroll container.
- In CSS, `z-index` orders positioned siblings; equal values fall back to source order.
- In CSS, transforms, opacity below 1, and filters spawn new stacking contexts that trap children.
- In CSS, `top/right/bottom/left` insets position only when `position` is non-static.
- In CSS, absolutely center with `inset: 0; margin: auto` on fixed-size boxes.
- In CSS, `overflow: hidden` on ancestors clips sticky and fixed descendants unexpectedly.
