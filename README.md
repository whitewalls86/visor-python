# visor-python

Python SDK for the [Visor Public API](https://api.visor.vin) — a car inventory
search platform covering new, used, and certified pre-owned vehicles.

## Install

```bash
pip install visor-python
```

## Quick start

```python
from visor import VisorClient, ListingsFilter

with VisorClient() as client:  # reads VISOR_API_KEY from env
    # Search for used Toyota trucks in Texas under $40k
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
        print(f"{listing.year} {listing.make} {listing.model} — ${listing.price:,}")

    # Look up a specific VIN
    vin = client.lookup_vin("4T1DAACKXTU765422", include=["price_history"])
    print(vin.build.combined_msrp)

    # Paginate all results
    from visor import iter_listings
    for listing in iter_listings(client, ListingsFilter(make=["Ford"], state=["TX"])):
        print(listing.vin)
```

## Async

```python
import asyncio
from visor import AsyncVisorClient, ListingsFilter

async def main():
    async with AsyncVisorClient() as client:
        page = await client.filter_listings(
            ListingsFilter(make=["Toyota"], state=["TX"], max_price=40_000)
        )
        for listing in page.data:
            print(listing.vin, listing.price)

asyncio.run(main())
```

## Auth

Pass your API key directly or set `VISOR_API_KEY` in the environment:

```python
client = VisorClient(api_key="vsr_live_...")
# or
# export VISOR_API_KEY=vsr_live_...
client = VisorClient()
```

## License

MIT
