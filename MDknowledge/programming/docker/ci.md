# Docker in CI

- Layer caching (`--cache-from` registry images) cuts CI build minutes drastically.
- Build once, tag with SHA, promote the same digest through environments.
- Run test suites inside the shipped image to test what actually deploys.
- Hadolint lints Dockerfiles for best-practice violations in CI gates.
- Trivy/Grype scans fail builds on critical CVEs before registries accept pushes.
- Multi-arch builds (`buildx`) ship arm64 plus amd64 from one pipeline.
- `.dockerignore` discipline keeps CI contexts small and fast to upload.
- Ephemeral registry credentials (OIDC) beat long-lived passwords in pipelines.
- Prune runners (`docker system prune -af`) to stop disk-full CI flakes.
- Pin action and base versions so pipelines reproduce months later.
