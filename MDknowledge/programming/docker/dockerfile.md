# Dockerfile authoring

- Start `FROM` pinned slim bases and declare `WORKDIR` before copying code.
- COPY requirements first, install, then copy code to cache dependency layers.
- Prefer `COPY` over `ADD`; `ADD` fetches URLs and unpacks unexpectedly.
- Run as non-root via `USER` after setup steps needing privileges.
- Combine `apt-get update && install && rm -rf /var/lib/apt/lists/*` in one layer.
- `ENV` bakes config; runtime `-e` flags override per environment.
- `EXPOSE` documents ports; `-p` publishing actually opens them.
- `HEALTHCHECK` lets orchestrators restart wedged containers automatically.
- `.dockerignore` node_modules/.git keeps contexts small and secret-free.
- `docker build --no-cache` verifies reproducibility when caches hide staleness.
