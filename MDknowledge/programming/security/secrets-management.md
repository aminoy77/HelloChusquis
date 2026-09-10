# Secrets management

- Vaults (HashiCorp Vault, cloud KMS/secrets managers) centralize credentials with audit trails.
- Inject secrets at runtime via env/files, never bake into images or repos.
- Short-lived dynamic credentials beat static passwords that leak and linger.
- Git history never forgets: rotate immediately on accidental commits plus purge.
- Pre-commit hooks (gitleaks, trufflehog) catch secrets before they land.
- Separate dev/staging/prod credentials so one leak cannot cross environments.
- Application identities (workload IAM) replace shared static keys between services.
- Audit secret access logs for anomalous reads like any sensitive data.
- Backup encryption keys offline (Shamir-split) against cloud lockout.
- Document rotation runbooks before incidents force improvisation.
