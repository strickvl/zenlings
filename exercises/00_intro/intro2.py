"""
Making a Pipeline Dynamic

A dynamic pipeline uses `dynamic=True` in the @pipeline decorator.
This enables runtime control flow - loops, conditionals, and more!

FIX: Add the `dynamic=True` parameter to the @pipeline decorator.
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


# TODO: Add dynamic=True to enable dynamic pipeline features
@pipeline
def my_first_dynamic_pipeline():
    """A pipeline that will become dynamic."""
    items = get_items()

    # Once dynamic=True is added, we'll be able to:
    # - Load artifact data with items.load()
    # - Use Python loops and conditionals
    # - Call step.map(), step.submit(), etc.

    # For now, just call the step once
    process_item("test")


if __name__ == "__main__":
    my_first_dynamic_pipeline()
