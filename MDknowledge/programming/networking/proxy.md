# Proxies

- Forward proxies fetch on clients' behalf, caching and filtering centrally.
- Reverse proxies (nginx, HAProxy) terminate TLS and balance backends.
- Transparent proxies intercept without client configuration at gateway chokepoints.
- CONNECT tunnels HTTPS through proxies opaquely to the destination.
- Proxy env vars (`HTTP_PROXY`, `NO_PROXY`) steer CLI tools consistently.
- PAC files route per-URL proxy decisions in browsers automatically.
- Caching proxies cut repeated downloads but must honor Cache-Control.
- Authenticated proxies gate contractor and guest traffic centrally.
- Misconfigured open proxies relay spam and attacks under your IP.
- Service meshes (Envoy sidecars) generalize proxies per microservice hop.
