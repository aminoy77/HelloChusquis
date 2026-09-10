# Two-factor authentication

- 2FA pairs knowledge (password) with possession (device) or inherence (biometrics).
- Authenticator TOTP apps beat SMS codes, which SIM-swapping defeats.
- Hardware keys (FIDO2/WebAuthn) resist phishing entirely via origin binding.
- Passkeys generalize hardware-key UX across phones and laptops.
- Backup codes (printed, offline) rescue locked-out users without helpdesk risk.
- Enroll 2FA at account creation, not as an optional later step.
- Remembered-device cookies need expiry plus re-verification on sensitive actions.
- Recovery flows must match primary strength or attackers route around 2FA.
- Mandate 2FA for admins, finance, and code-signing roles first.
- Monitor impossible-travel and velocity anomalies atop static factors.
