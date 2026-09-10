# Containers vs VMs

- Containers share the host kernel; VMs virtualize full guest operating systems.
- Containers start in milliseconds; VMs boot in tens of seconds.
- Container images layer and deduplicate; VM disks duplicate whole systems.
- VMs isolate kernels (stronger); containers isolate processes (lighter).
- Run untrusted multi-tenant workloads in VMs or microVMs (Firecracker), not plain containers.
- Kubernetes orchestrates containers; hypervisors (KVM, Hyper-V) manage VMs.
- Docker Desktop virtualizes Linux on Mac/Windows underneath containers transparently.
- Namespaces (pid, net, mnt) plus cgroups build container isolation from kernel primitives.
- Serverless often wraps microVMs for container ergonomics with VM boundaries.
- Choose VMs for kernel diversity, containers for density and speed.
