# npm essentials

- `npm init -y` scaffolds package.json; `npm install` resolves node_modules.
- `npm install pkg` saves runtime deps; `-D` marks dev-only tooling.
- `package-lock.json` pins transitive trees — always commit it for apps.
- Semver ranges (`^1.2.3`) float minors; lockfiles freeze exact installs.
- `npm run <script>` executes package.json scripts with local binaries first.
- `npx pkg` runs one-off binaries without global installs polluting systems.
- `npm outdated` plus `npm audit` surface stale and vulnerable dependencies.
- `npm ci` installs lockfile-exact for reproducible CI pipelines.
- Workspaces (`npm init -w`) coordinate monorepo packages with shared deps.
- Never commit node_modules; `.gitignore` it universally.
