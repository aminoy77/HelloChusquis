# Contributing to HelloChusquis

Thank you for your interest in contributing! 🎉

## Ways to Contribute

- **Report bugs** — open an issue with steps to reproduce
- **Suggest features** — open an issue describing your idea
- **Submit plugins** — contribute to [OpenManolo-plugins](https://github.com/aminoy77/OpenManolo-plugins)
- **Improve docs** — fix typos, add examples, clarify steps
- **Submit code** — open a pull request

## Getting Started

```bash
git clone https://github.com/aminoy77/HelloChusquis.git
cd HelloChusquis
pip install -e .
hellochusquis
```

## Submitting a Pull Request

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test that `hellochusquis` still works
5. Commit: `git commit -m "add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request on GitHub

## Submitting a Plugin

Plugins live in a separate repo: [OpenManolo-plugins](https://github.com/aminoy77/OpenManolo-plugins)

Each plugin is a single `.py` file following this structure:

```python
PLUGIN_NAME = "name"
PLUGIN_DESCRIPTION = "What it does"
PLUGIN_SCHEMA = { ... }

def run(**kwargs) -> str:
    return "result"
```

See existing plugins for examples.

## Code Style

- Python 3.10+
- Keep it simple — no unnecessary dependencies
- Every function must handle exceptions gracefully
- Test before submitting
