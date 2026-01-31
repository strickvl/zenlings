"""
Loading Artifacts - Exercise 2: Loop Based on Loaded Count

CONCEPT: A common pattern is to:
         1. Run a step that returns a count or list
         2. Load the result
         3. Use Python control flow based on that data

TASK: Complete the pipeline body to process each item dynamically.

The pipeline should:
1. Get the items from the step
2. Load the items to access the list
3. Loop through each item and call process_item for each
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
    # TODO: Complete this pipeline
    # 1. Call get_items() to get the artifact
    # 2. Load the artifact to get the actual list
    # 3. Loop through each item and call process_item(item)
    pass


if __name__ == "__main__":
    load2_pipeline()
