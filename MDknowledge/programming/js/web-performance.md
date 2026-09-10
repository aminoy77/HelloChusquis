# Web performance

- Core Web Vitals (LCP, INP, CLS) gate search ranking and UX quality.
- LCP (largest paint) improves via preloads, compression, and edge caching.
- INP (interaction latency) drops by yielding long tasks under 50ms slices.
- CLS (layout shift) vanishes with sized media and reserved ad slots.
- Code-split routes so initial bundles carry only first-paint code.
- Images: modern formats (AVIF/WebP), responsive `srcset`, lazy below fold.
- Fonts: `font-display: swap` plus subsetting prevent invisible text.
- Third-party scripts sandbox in facades loading on interaction.
- HTTP caching (`immutable` hashed assets) makes revisits instant.
- Measure field data (CrUX/RUM), not just lab Lighthouse scores.
