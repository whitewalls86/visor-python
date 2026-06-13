# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-13

### Added

- Initial package scaffold: exceptions, filter models, response models
- `visor.exceptions` — typed exception hierarchy
- `visor.models._base` — shared building blocks and `ListingsFilterBase`
- `visor.models.listings` — `ListingsFilter` and listing response models
- `visor.models.facets` — `FacetsFilter` and facet response models
- `AsyncVisorClient` — async HTTP client with context-manager support
- `VisorClient` — synchronous HTTP client with context-manager support
- Auto-pagination helpers: `paginate_listings`, `paginate_dealers` (async generators),
  `iter_listings`, `iter_dealers` (sync iterators)
- Public export audit and test suite (`tests/test_exports.py`)
- `src/visor/py.typed` PEP 561 marker for typed-package distribution
- Publish-grade `pyproject.toml` metadata: authors, classifiers, keywords, license files, URLs
- CI matrix across Python 3.10–3.13 with separate lint, test, and build jobs

[Unreleased]: https://github.com/whitewalls86/visor-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/whitewalls86/visor-python/releases/tag/v0.1.0
