# Docker security

- Run containers as non-root users to blunt breakout impact.
- Read-only filesystems plus dropped capabilities (`--cap-drop=all`) harden runtimes.
- Scan images for CVEs in CI and rebuild on base-image updates.
- Secrets belong in managers or mounted files, never env vars or layers.
- User namespaces remap root inside containers away from host root.
- seccomp/AppArmor profiles constrain syscalls beyond default filters.
- Image signatures (cosign) verify provenance before deployment.
- Resource quotas blunt fork-bomb and memory-exhaustion denial of service.
- Keep daemon sockets off networks; local socket access equals root.
- Minimal distroless bases remove shells attackers would reach for.
