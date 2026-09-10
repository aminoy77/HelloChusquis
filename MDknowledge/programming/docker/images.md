# Docker images

- Images are layered read-only templates; containers are their runnable instances.
- Dockerfiles build images deterministically from versioned base images.
- Order Dockerfile steps slow-changing first to maximize layer-cache hits.
- Pin base tags (`python:3.12-slim`) instead of floating `latest` for reproducibility.
- Multi-stage builds compile in fat images then ship slim runtimes.
- `.dockerignore` excludes secrets and build context bloat like `.git`.
- `docker images` lists locals; `docker rmi` prunes unneeded ones.
- Small bases (alpine/slim/distroless) shrink attack surface and pull times.
- Never bake secrets into layers; history preserves them forever — use build secrets.
- Scan images (`docker scout`) for CVEs before promoting to production.
