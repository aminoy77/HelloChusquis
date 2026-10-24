"""Tests for the --login CLI flag helpers."""
from cli import resolve_login_name


def test_alias_resolution():
    assert resolve_login_name("copilot") == "GitHub Copilot"
    assert resolve_login_name("ghc") == "GitHub Copilot"
    assert resolve_login_name("GitHub Copilot") == "GitHub Copilot"
    assert resolve_login_name("qwen") == "Qwen"
    assert resolve_login_name("QWEN") == "Qwen"


def test_unknown_name_returns_none():
    assert resolve_login_name("nope") is None
    assert resolve_login_name("") is None
