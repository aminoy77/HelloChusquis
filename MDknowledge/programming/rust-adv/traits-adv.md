# Rust advanced traits (example)

- Associated types (`type Item`) bind outputs to traits without extra params.
- Generic associated types (GATs) parameterize associated types by lifetimes.
- Trait objects (`dyn Trait`) trade static dispatch for runtime flexibility.
- Auto traits (`Send/Sync`) propagate through composition automatically.
- Negative impls (unstable) would opt types out of auto traits eventually.
- Sealed traits (private supertraits) close extension points deliberately.
- Blanket impls (`impl<T: Display> Foo for T`) cover families at once.
- Coherence/orphan rules prevent conflicting downstream impls soundly.
- Extension traits add methods to foreign types idiomatically.
- Const traits (incomplete feature) promise compile-time evaluation eventually.
