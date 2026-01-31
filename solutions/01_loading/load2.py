"""
Loading Artifacts - Exercise 2: Solution

The pattern: get artifact -> load data -> use in Python control flow.
"""

from zenml import pipeline, step


@step
def get_items() -> list[str]:
    """Returns a list of items to process."""
    return ["apple", "banana", "cherry", "date"]


@step
def process_item(item: str) -> str:
    """Process a single item."""
    result = f"Processed: {item.upper()}"
    print(result)
    return result


@pipeline(dynamic=True)
def load2_pipeline():
    # SOLUTION:
    # 1. Get the artifact reference
    items = get_items()

    # 2. Load to get actual list data
    items_data = items.load()

    # 3. Loop and process each item
    for item in items_data:
        process_item(item)


if __name__ == "__main__":
    load2_pipeline()
