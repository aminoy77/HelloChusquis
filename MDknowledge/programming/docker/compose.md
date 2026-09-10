# Docker Compose

- `docker compose up -d` launches multi-service stacks from compose.yaml.
- Services declare images/builds, ports, volumes, and `depends_on` ordering.
- Environment files (`.env`) separate secrets from committed compose files.
- `docker compose logs -f svc` tails one service in noisy stacks.
- `docker compose down` stops and removes; `-v` also drops named volumes.
- Profiles (`--profile gpu`) toggle optional services per environment.
- Healthcheck `depends_on: condition: service_healthy` sequences startups correctly.
- Override files (`compose.override.yaml`) layer local tweaks atop shared bases.
- Resource limits per service prevent one container starving neighbors.
- `docker compose pull` pre-fetches images for fast zero-downtime redeploys.
