# CSS selectors

- In CSS, `.class` targets classes, `#id` targets ids, and `tag` targets element types.
- In CSS, descendant `A B` matches any depth while child `A > B` matches direct children only.
- In CSS, adjacent `A + B` hits the next sibling and general `A ~ B` hits all later siblings.
- In CSS, `[attr='v']` matches attributes with `^=`, `$=`, `*=` variants for prefix/suffix/substring.
- In CSS, `:first-child`/`:last-child` hit edges and `:nth-child(2n)` hits patterned positions.
- In CSS, `:not(.x)` excludes matches and chains for precise targeting.
- In CSS, `A, B` groups selectors sharing one declaration block.
- In CSS, `*` matches everything; scope it (`article *`) to avoid global costs.
- In CSS, pseudo-elements `::before`/`::after` inject decorative content with `content: ''`.
- In CSS, `:focus-visible` styles keyboard focus without mouse-click outlines.
