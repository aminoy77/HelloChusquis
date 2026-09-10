# Docker volumes

- Volumes persist data beyond container lifetimes, unlike writable layers.
- Named volumes (`-v data:/var/lib/db`) outlive containers and migrate cleanly.
- Bind mounts (`-v ./src:/app`) sync host code into dev containers live.
- Anonymous volumes die with containers unless explicitly preserved.
- `docker volume ls/inspect/prune` manage orphaned storage proactively.
- Back up named volumes with throwaway tar containers before upgrades.
- Read-only mounts (`:ro`) protect configs from container writes.
- Database containers must mount volumes or restarts wipe all data.
- Volume drivers (NFS, cloud) share state across multi-host clusters.
- `tmpfs` mounts hold ephemeral scratch in RAM without disk wear.
