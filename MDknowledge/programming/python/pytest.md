# Python pytest

- pytest discovers `test_*.py` files and `test_*` functions with zero boilerplate.
- Plain `assert` statements produce rich introspection on failure automatically.
- Fixtures (`@pytest.fixture`) inject setup with function/module/session scopes.
- `parametrize` multiplies one test across input matrices declaratively.
- `tmp_path` supplies per-test temporary directories auto-cleaned afterward.
- `monkeypatch` fakes env vars and attributes with automatic teardown.
- `pytest.raises` asserts exceptions plus message matching in context blocks.
- `-k` selects subsets by name expression for focused reruns.
- `-x` stops at first failure; `-q` quiets output for CI logs.
- Coverage plugins (`--cov`) gate untested code from merging.
