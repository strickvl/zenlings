"""
Configuration - Exercise 1: Dynamic Step Configuration with with_options()

CONCEPT: Use step.with_options() to dynamically configure steps at runtime.
         This lets you change settings like:
         - enable_cache: Whether to use cached results
         - step_operator: Which infrastructure to use
         - extra: Custom metadata
         - And more!

         Syntax:
           step.with_options(
               enable_cache=False,
               extra={"key": "value"}
           )(param1, param2)

TASK: Complete the pipeline to run the same step with different configs:
      1. Run process_data with caching enabled (default)
      2. Run process_data with caching disabled (fresh run)
      3. Run process_data with custom metadata
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_data() -> list[int]:
    """Get data to process."""
    return [1, 2, 3, 4, 5]


@step(enable_cache=False)
def process_data(data: list[int], mode: str) -> int:
    """Process data and return sum."""
    total = sum(data)
    print(f"Mode: {mode}, Processing {len(data)} items, sum = {total}")
    return total


@pipeline(dynamic=True)
def config1_pipeline():
    data = get_data()

    # TODO: Complete this pipeline
    #
    # 1. Call process_data normally (caching enabled by default)
    #    process_data(data, "cached")
    #
    # 2. Call process_data with caching DISABLED
    #    Use: process_data.with_options(enable_cache=False)(data, "fresh")
    #
    # 3. Call process_data with custom metadata
    #    Use: process_data.with_options(extra={"priority": "high"})(data, "priority")

    pass


if __name__ == "__main__":
    config1_pipeline()
