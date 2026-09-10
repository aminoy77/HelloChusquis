# CSS typography

- In CSS, `font-family` stacks fallbacks ending in generic `serif`/`sans-serif`/`monospace`.
- In CSS, `font-size` in `rem` scales with root settings for accessible zoom.
- In CSS, `line-height` unitless values (1.5) scale with font size unlike fixed lengths.
- In CSS, `font-weight: 400/700` maps regular/bold; variable fonts interpolate between.
- In CSS, `letter-spacing` and `word-spacing` fine-tune density of headings and labels.
- In CSS, `text-align: justify` needs hyphenation to avoid rivers of whitespace.
- In CSS, `text-overflow: ellipsis` with `overflow: hidden` and `white-space: nowrap` truncates lines.
- In CSS, `line-clamp` (with `-webkit-` prefix combo) truncates multi-line excerpts cleanly.
- In CSS, system font stacks (`system-ui, ...`) render natively fast with zero downloads.
- In CSS, `font-display: swap` in `@font-face` shows fallback text while webfonts load.
