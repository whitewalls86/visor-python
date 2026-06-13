# Contributing

Contributions are welcome. Please open an issue before starting significant work
so we can discuss the approach.

## Setup

```bash
git clone https://github.com/whitewalls86/visor-python
cd visor-python
pip install -e ".[dev]"
```

## Running checks

```bash
pytest
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

## Pull requests

- Keep PRs focused — one logical change per PR.
- All tests must pass and mypy must be clean before merging.
- Add a `CHANGELOG.md` entry under `[Unreleased]`.

## Versioning and releases

This package follows [Semantic Versioning](https://semver.org/) and
[PEP 440](https://peps.python.org/pep-0440/) version strings.

- The package is pre-1.0 (`0.x`). Minor version bumps may include breaking changes.
- Release tags use a `v` prefix — e.g. `v0.1.0`, `v0.2.0`.
- After `v1.0.0`, breaking changes require a major version bump.
- Version is set in `pyproject.toml`. Do not version-bump in a feature PR;
  maintainers handle releases separately.
