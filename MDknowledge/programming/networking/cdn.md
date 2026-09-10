# CDN essentials

- CDNs cache content at edge PoPs near users, slashing latency worldwide.
- Static assets (images, JS, CSS) gain most; personalize via edge includes carefully.
- Cache keys (URL, headers, cookies) decide hit rates; normalize ruthlessly.
- TTL hierarchies (browser, edge, origin shield) layer freshness guarantees.
- Purge APIs invalidate instantly on deploys instead of waiting out TTLs.
- Anycast routes users to nearest healthy PoP automatically.
- Origin shield tiers absorb thundering herds before backends feel them.
- Signed URLs/cookies gate premium content at the edge.
- WAF plus DDoS absorption come bundled with major CDN platforms.
- Measure cache-hit ratio; low ratios mean keys or TTLs need work.
