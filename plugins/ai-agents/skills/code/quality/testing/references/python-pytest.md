# Python — pytest

- Use **pytest** and **pytest-mock** only. Do not import `unittest.mock`.
- Prefer **`tmp_path`** or the **`pyfakefs` `fs` fixture** over creating real files in the repo tree.
- Shared fixtures live under `tests/fixtures/` (or the path the repo already uses). Import or register them — do not paste setup into each file.
- Use `@pytest.mark.parametrize` for edge cases (empty, quoted, prefixed, missing file).
- Mock GitPython / subprocess / GitHub HTTP at the boundary with `mocker`. Do not mock the function you are testing.
- Type-annotate test helpers and fixtures. Google-style docstrings on non-obvious fixtures.

```python
def test_parse_quoted_version(tmp_path: Path) -> None:
    target = tmp_path / "version.txt"
    target.write_text('"1.2.3"\n', encoding="utf-8")
    assert parse_version(target) == "1.2.3"
```

All generated tests must pass the repo Validate suite (`ruff`, `ruff format`, `mypy` when listed, `pytest`).
