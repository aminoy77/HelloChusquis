# Load balancing

- Load balancers spread traffic for scale and failover across backends.
- Round-robin suits uniform nodes; least-connections favors uneven capacities.
- IP-hash stickiness pins sessions where apps keep local state.
- Health checks eject dead backends before users notice errors.
- Layer-4 balancing is fast and dumb; Layer-7 routes on URLs and headers.
- Sticky sessions are a crutch; externalize state to scale freely.
- Connection draining lets deploys finish in-flight requests before shutdown.
- Global (DNS/anycast) balancing survives whole-region outages.
- Autoscaling pairs with balancers to grow pools under load metrics.
- Test failure modes (backend death, slowloris) not just happy-path throughput.
