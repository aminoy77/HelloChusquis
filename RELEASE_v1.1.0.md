---
## HelloChusquis v1.1.0 — Config Command

### What's New

**Config Command**
You can now reconfigure HelloChusquis anytime with the new config command:

```bash
hellochusquis config              # Full setup wizard
hellochusquis config --show       # Show current config (masked keys)
hellochusquis config --api-keys  # Edit only API keys
hellochusquis config --providers # Edit only providers
```

Current values are shown as defaults — just press Enter to keep them.

### Bug Fixes
- Fixed `hellochusquis web` command not working
- Fixed CLI module import issues
- Added proper workspace package to pyproject.toml

### Install

```bash
pip install hellochusquis
```

### Upgrade

```bash
pip install --upgrade hellochusquis
```

### Note
This is v1.1.0. Things will break. Open an issue when they do.