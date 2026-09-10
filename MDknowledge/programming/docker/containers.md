# Docker containers

- `docker run -d --name web -p 8080:80 img` detaches named, port-mapped containers.
- `docker ps` lists running and `docker ps -a` includes stopped ones for cleanup.
- `docker logs -f` tails output; `--tail 100` bounds initial history.
- `docker exec -it c sh` opens shells inside running containers for inspection.
- `docker stop` signals gracefully (10s) before `docker kill` forces termination.
- Restart policies (`--restart unless-stopped`) revive crashed services automatically.
- `docker rm` deletes stopped containers; `docker container prune` sweeps all stopped.
- Resource flags (`--memory`, `--cpus`) cap noisy neighbors on shared hosts.
- Read-only roots (`--read-only` + tmpfs) harden compromised containers.
- One concern per container; compose multi-service systems instead.
