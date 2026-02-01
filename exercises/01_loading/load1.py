"""
Loading Artifacts - Exercise 1: Your First .load()

CONCEPT: In dynamic pipelines, step outputs are artifact REFERENCES, not data.
         To access the actual data, call .load() on the artifact.

THE BUG: This pipeline crashes because we try to use an artifact reference
         directly as if it were an integer.

FIX: Use .load() to get the actual count value before using it in range().
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_count() -> int:
    """Returns the number of items to process."""
    return 5


@step(enable_cache=False)
def process_item(index: int) -> str:
    """Process a single item by index."""
    result = f"Processed item {index}"
    print(result)
    return result


@pipeline(dynamic=True)
def load1_pipeline():
    count = get_count()  # This returns an OutputArtifact, NOT an int!

    # TODO: Fix this line - you need to load the artifact data first
    # Currently crashes: TypeError: 'OutputArtifact' object cannot be interpreted as an integer
    for i in range(count):
        process_item(i)


if __name__ == "__main__":
    load1_pipeline()
