"""
Loading Artifacts - Exercise 1: Solution

The fix is to call .load() on the artifact to get the actual integer value.
"""

from zenml import pipeline, step


@step
def get_count() -> int:
    """Returns the number of items to process."""
    return 5


@step
def process_item(index: int) -> str:
    """Process a single item by index."""
    result = f"Processed item {index}"
    print(result)
    return result


@pipeline(dynamic=True)
def load1_pipeline():
    count = get_count()

    # SOLUTION: Load the artifact data before using it
    count_value = count.load()  # Now we have the actual integer!

    for i in range(count_value):
        process_item(i)


if __name__ == "__main__":
    load1_pipeline()
