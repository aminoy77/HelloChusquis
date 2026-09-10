# Docker debugging

- `docker logs --tail 200 svc` surfaces recent crashes without drowning output.
- `docker exec -it c sh` inspects live filesystems, env, and processes.
- `docker inspect c` dumps config, mounts, networks, and health verbatim.
- `docker stats` streams CPU/memory per container for hog hunts.
- `docker events` tails daemon activity during flaky orchestration.
- Copy files out with `docker cp c:/path ./local` for offline analysis.
- Reproduce with `--entrypoint sh` overriding broken default commands.
- Bump log verbosity via daemon.json or service command flags temporarily.
- `docker system df` attributes disk to images, containers, and volumes.
- Bisect with `docker compose up one-service` to isolate failing members.
