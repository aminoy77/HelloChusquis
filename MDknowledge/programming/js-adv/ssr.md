# Server-side rendering (example)

- SSR renders HTML per request for SEO plus fast first paint.
- Hydration attaches interactivity to server markup client-side.
- Mismatches (server/client HTML drift) warn loudly — fix data fetching.
- Static generation prebuilds pages at deploy for CDN-served speed.
- ISR revalidates static pages on schedules balancing fresh and fast.
- Streaming SSR flushes shell HTML before data resolves progressively.
- Server components (React) keep data access off client bundles.
- Caching headers decide SSR cost per request versus stale tolerance.
- Edge rendering moves SSR near users cutting latency globally.
- Client-only fallbacks (`dynamic ssr:false`) escape SSR-hostile widgets.
