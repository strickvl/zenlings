"""
Async Execution - Exercise 4: Fan-Out and Fan-In Pattern

CONCEPT: A common parallel pattern:
         - Fan-out: Launch multiple steps in parallel
         - Fan-in: Collect all results into one aggregator step

         Pattern:
           # Fan-out: launch N parallel tasks
           futures = [process.submit(item) for item in items]

           # Fan-in: aggregate waits for all
           aggregate.submit(after=futures)

TASK: Build a fan-out/fan-in pipeline from scratch that:
      1. Gets a list of URLs (simulated)
      2. Fans out to fetch each URL in parallel
      3. Fans in to aggregate all results
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
    # Simulate fetching - in real life this would make HTTP requests
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

    # TODO: Build the fan-out/fan-in pattern
    #
    # 1. Load the URLs to iterate over them
    # 2. Fan-out: Create a list of futures by submitting fetch_url for each URL
    #    futures = [fetch_url.submit(url=...) for url in urls_data]
    # 3. Fan-in: Submit aggregate_responses with after=futures
    #    Note: You'll also need to collect the results to pass to aggregate
    #
    # Hint: You can use .map() for this too, but try the manual fan-out pattern!

    pass


if __name__ == "__main__":
    async4_pipeline()
