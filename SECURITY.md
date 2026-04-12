# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.6.x | ✅ |
| < 0.6 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability, **do not open a public issue**.

Instead, report it privately by:
1. Going to the [Security tab](https://github.com/aminoy77/HelloChusquis/security) on GitHub
2. Clicking **"Report a vulnerability"**

We will respond within 48 hours and work on a fix as quickly as possible.

## Security Considerations

- HelloChusquis has access to your file system within allowed directories
- Shell commands are executed directly — only run on trusted machines
- API keys are stored in `config.yaml` — never commit this file
- The `config.yaml` is in `.gitignore` by default
