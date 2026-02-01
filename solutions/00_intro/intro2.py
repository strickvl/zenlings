"""
Making a Pipeline Dynamic - Solution

The fix is to add dynamic=True to the @pipeline decorator.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_items() -> list[str]:
    """Returns a list of items to process."""
    return ["apple", "banana", "cherry"]


@step(enable_cache=False)
def process_item(item: str) -> str:
    """Process a single item."""
    result = f"Processed: {item.upper()}"
    print(result)
    return result


# SOLUTION: Added dynamic=True
@pipeline(dynamic=True)
def my_first_dynamic_pipeline():
    """A pipeline that will become dynamic."""
    items = get_items()

    # Now that dynamic=True is added, we can:
    # - Load artifact data with items.load()
    # - Use Python loops and conditionals
    # - Call step.map(), step.submit(), etc.

    # For now, just call the step once
    process_item("test")


if __name__ == "__main__":
    my_first_dynamic_pipeline()
