# JS bundlers (example)

- Bundlers resolve, transform, and tree-shake modules into deployable assets.
- Vite serves ESM natively in dev, Rollup-bundles for production.
- Code-splitting (`import()`) defers routes below first-paint budgets.
- Tree-shaking drops unused exports guided by `sideEffects` flags.
- Content-hashed filenames (`app.[hash].js`) cache-bust safely forever.
- Sourcemaps map minified traces back to authors' code in production.
- Bundle analyzers visualize dependency weight driving diet decisions.
- Transpilation targets (browserslist) balance syntax support versus bytes.
- Long-term caching splits vendor chunks from app code deliberately.
- Measure with real devices/throttling; lab machines flatter bundles.
