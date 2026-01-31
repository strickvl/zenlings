"""
Async Execution - Exercise 4: Solution

Fan-out/fan-in is a powerful pattern for parallel processing.
Launch many tasks, wait for all, then aggregate.
"""

from zenml import pipeline, step


@step
def get_urls() -> list[str]:
    """Get URLs to fetch."""
    return [
        "https://api.example.com/data1",
        "https://api.example.com/data2",
        "https://api.example.com/data3",
        "https://api.example.com/data4",
    ]


@step
def fetch_url(url: str) -> dict:
    """Fetch data from a URL (simulated)."""
    import hashlib
    fake_data = {
        "url": url,
        "status": 200,
        "size": int(hashlib.md5(url.encode()).hexdigest()[:4], 16)
    }
    print(f"Fetched {url} -> size={fake_data['size']}")
    return fake_data


@step
def aggregate_responses(responses: list[dict]) -> None:
    """Aggregate all fetched responses."""
    print(f"\n=== Aggregated {len(responses)} responses ===")
    total_size = sum(r["size"] for r in responses)
    print(f"Total data size: {total_size}")
    for r in responses:
        print(f"  {r['url']}: {r['size']} bytes")


@pipeline(dynamic=True)
def async4_pipeline():
    urls = get_urls()

    # SOLUTION:
    # 1. Load URLs to iterate
    urls_data = urls.load()

    # 2. Fan-out: Submit a fetch for each URL in parallel
    futures = []
    for url in urls_data:
        future = fetch_url.submit(url=url)
        futures.append(future)
    # All 4 fetches are now running in parallel!

    # 3. Fan-in: Collect results and aggregate
    # Load all results (this waits for each to complete)
    responses = [f.load() for f in futures]

    # Pass to aggregator
    aggregate_responses(responses)

    # Alternative using .map() (simpler but less explicit):
    # responses = fetch_url.map(url=urls)
    # aggregate_responses(responses)


if __name__ == "__main__":
    async4_pipeline()
