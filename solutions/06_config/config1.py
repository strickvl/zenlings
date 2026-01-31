"""
Configuration - Exercise 1: Solution

with_options() lets you configure steps dynamically at runtime.
Each call can have different settings.
"""

from zenml import pipeline, step


@step
def get_data() -> list[int]:
    """Get data to process."""
    return [1, 2, 3, 4, 5]


@step
def process_data(data: list[int], mode: str) -> int:
    """Process data and return sum."""
    total = sum(data)
    print(f"Mode: {mode}, Processing {len(data)} items, sum = {total}")
    return total


@pipeline(dynamic=True)
def config1_pipeline():
    data = get_data()

    # SOLUTION:
    # 1. Normal call with default caching
    result1 = process_data(data, "cached")

    # 2. Call with caching disabled - forces fresh execution
    result2 = process_data.with_options(
        enable_cache=False
    )(data, "fresh")

    # 3. Call with custom metadata attached
    result3 = process_data.with_options(
        extra={"priority": "high", "team": "ml-ops"}
    )(data, "priority")

    # Note: All three runs will execute, and you can inspect
    # their configurations in the ZenML dashboard


if __name__ == "__main__":
    config1_pipeline()
