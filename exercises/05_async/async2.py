"""
Async Execution - Exercise 2: .result() vs .load()

CONCEPT: Futures have two ways to get their data:
         - .result() returns the OutputArtifact (metadata + reference)
         - .load() returns the actual data

         Use .result() when you need artifact metadata or want to pass
         the artifact reference to another step.

         Use .load() when you need the actual data for Python operations.

TASK: Complete the pipeline to demonstrate both methods:
      1. Submit a step that returns a number
      2. Use .result() to get the artifact (for logging metadata)
      3. Use .load() to get the actual number (for calculation)
"""

from zenml import pipeline, step


@step(enable_cache=False)
def compute_value() -> int:
    """Compute a value."""
    value = 42
    print(f"Computed value: {value}")
    return value


@step(enable_cache=False)
def double_value(x: int) -> int:
    """Double a value."""
    result = x * 2
    print(f"Doubled: {x} * 2 = {result}")
    return result


@pipeline(dynamic=True)
def async2_pipeline():
    # TODO: Complete this pipeline
    # 1. Submit compute_value() to get a future
    # 2. Use .result() to get the OutputArtifact
    #    Print something about the artifact (e.g., its type)
    # 3. Use .load() to get the actual integer value
    #    Use it in a Python calculation (e.g., add 10)
    # 4. Pass the future to double_value() to show artifact passing

    pass


if __name__ == "__main__":
    async2_pipeline()
