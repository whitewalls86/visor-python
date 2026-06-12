# Contributing

Contributions are welcome. Please open an issue before starting significant work
so we can discuss the approach.

## Setup

```bash
git clone https://github.com/drewpearce/visor-python
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
