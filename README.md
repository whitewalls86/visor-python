# visor-python

[![CI](https://github.com/whitewalls86/visor-python/actions/workflows/ci.yml/badge.svg)](https://github.com/whitewalls86/visor-python/actions/workflows/ci.yml)

**visor-python** is the official Python SDK for the [Visor Public API](https://api.visor.vin) — a vehicle inventory search platform covering new, used, and certified pre-owned listings from dealers across the US. It provides a thin, fully-typed wrapper around the REST API with sync and async clients, Pydantic response models, and auto-pagination helpers.

> **Pre-1.0 notice:** This package is in initial development (`0.x`). Minor version bumps may include breaking changes. Pin to a specific minor version in production and review the [CHANGELOG](CHANGELOG.md) before upgrading.

## Install

```bash
pip install visor-python
```

Requires Python 3.10+ and no non-standard runtime dependencies beyond `httpx` and `pydantic`.

## Quick start

```python
from visor import VisorClient, ListingsFilter, iter_listings

with VisorClient() as client:  # reads VISOR_API_KEY from env
    # Search for used Toyota Tacomas in Texas under $40k
    page = client.filter_listings(
        ListingsFilter(
            make=["Toyota"],
            model=["Tacoma"],
            inventory_type=["used"],
            state=["TX"],
            max_price=40_000,
        )
    )
    for listing in page.data:
        price = f"${listing.price:,}" if listing.price is not None else "N/A"
        print(f"{listing.year} {listing.make} {listing.model} — {price}")

    # Look up a specific VIN
    vin = client.lookup_vin("4T1DAACKXTU765422", include=["price_history"])
    msrp = f"${vin.build.combined_msrp:,}" if vin.build.combined_msrp is not None else "N/A"
    print(msrp)
```

### Geo filtering

Pass a `postal_code` and `radius` (miles) to search near a location:

```python
page = client.filter_listings(
    ListingsFilter(
        make=["Honda"],
        model=["CR-V"],
        postal_code="90210",
        radius=50,
    )
)
```

`radius` requires a geo anchor (`postal_code`, `latitude`/`longitude`, or `dealer_id`). Passing `radius` alone raises `ValueError` before any network call.

### Paginating all results

`iter_listings` (sync) and `paginate_listings` (async) iterate every page automatically:

```python
from visor import VisorClient, ListingsFilter, iter_listings

with VisorClient() as client:
    for listing in iter_listings(
        client,
        ListingsFilter(make=["Ford"], state=["TX"]),
    ):
        print(listing.vin, listing.price)
```

For dealers, use `iter_dealers` / `paginate_dealers` in the same way.

`client.filter_listings(...)` returns a single page (`ListingsPage`). Use the
`iter_*` / `paginate_*` helpers when you need all results.

### Async

```python
import asyncio
from visor import AsyncVisorClient, ListingsFilter, paginate_listings

async def main() -> None:
    async with AsyncVisorClient() as client:
        # Single page
        page = await client.filter_listings(
            ListingsFilter(make=["Toyota"], state=["TX"], max_price=40_000)
        )
        for listing in page.data:
            price = f"${listing.price:,}" if listing.price is not None else "N/A"
            print(listing.vin, price)

        # All pages
        async for listing in paginate_listings(
            client,
            ListingsFilter(make=["Toyota"], state=["TX"]),
        ):
            print(listing.vin)

asyncio.run(main())
```

## Configuration

### API key

Pass your key explicitly or export `VISOR_API_KEY` before running:

```python
client = VisorClient(api_key="vsr_live_...")
# or
# export VISOR_API_KEY=vsr_live_...
client = VisorClient()
```

API keys are available from Visor — see [api.visor.vin](https://api.visor.vin) for details.

### Timeout

Default request timeout is 30 seconds. Override at construction time:

```python
client = VisorClient(timeout=10.0)
```

### Base URL (advanced)

`base_url` defaults to the production API. Override it for local testing or staging:

```python
client = VisorClient(base_url="http://localhost:8080")
```

## Key concepts

### `ListingsFilter` is shared

`ListingsFilter` is accepted by both `filter_listings()` and `dealer_inventory()`. Build one filter object and reuse it across both methods.

### `fields` is response projection, not filtering

`ListingsFilter.fields` controls which fields the API returns — it does not filter which listings match. Example:

```python
filter = ListingsFilter(
    make=["Toyota"],
    fields=["vin", "price", "mileage"],
)
```

`id` and `vin` are always returned by the API regardless of the `fields` projection.

### Responses are Pydantic models

All responses — `ListingsPage`, `ListingDetail`, `VinDetail`, etc. — are Pydantic v2 models. Access fields as attributes and use standard Pydantic methods (`.model_dump()`, `.model_json_schema()`, etc.) as needed.

## Error handling

All methods raise typed exceptions from `visor.exceptions`. The SDK does not retry automatically — `RateLimitError.retry_after` gives you the hint to build your own retry logic.

```python
import time
from visor import VisorClient, ListingsFilter, RateLimitError, VisorAPIError

def fetch_with_backoff(client: VisorClient, f: ListingsFilter) -> object:
    for attempt in range(4):
        try:
            return client.filter_listings(f)
        except RateLimitError as e:
            wait = e.retry_after if e.retry_after is not None else 2 ** attempt
            print(f"Rate limited — waiting {wait}s")
            time.sleep(wait)
        except VisorAPIError as e:
            raise  # surface non-rate-limit errors immediately
    raise RuntimeError("Exhausted retries")
```

Exception hierarchy:

| Exception | When |
|---|---|
| `VisorAPIError` | Base for all API errors; has `.status_code` |
| `AuthenticationError` | 401 — invalid or missing API key |
| `NotFoundError` | 404 — resource does not exist |
| `RateLimitError` | 429 — includes `.retry_after` (seconds, or `None`) |

## Debugging

**Inspect the exception** — `VisorAPIError` carries `.status_code` and a message from the API.

**Check `retry_after`** — for `RateLimitError`, `.retry_after` is the number of seconds to wait (or `None` if the API did not provide a value).

**Request-level logging** — visor-python uses `httpx` internally. Enable httpx logging to see raw requests and responses:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

## Community

- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community standards
- [GitHub Issues](https://github.com/whitewalls86/visor-python/issues) — bug reports and feature requests

## License

MIT
