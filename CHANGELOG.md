# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial package scaffold: exceptions, filter models, response models
- `visor.exceptions` — typed exception hierarchy
- `visor.models._base` — shared building blocks and `ListingsFilterBase`
- `visor.models.listings` — `ListingsFilter` and listing response models
- `visor.models.facets` — `FacetsFilter` and facet response models

## Future Work

- HTTP client (`AsyncVisorClient`, `VisorClient`)
- Auto-pagination helpers
- Retry-with-backoff strategy
- MCP server wrapper
- Response caching
