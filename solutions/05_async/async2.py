"""
Async Execution - Exercise 2: Solution

.result() gives you the artifact reference (OutputArtifact).
.load() gives you the actual data inside the artifact.
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
    # SOLUTION:
    # 1. Submit to get a future
    future = compute_value.submit()

    # 2. Use .result() to get the OutputArtifact
    # This gives you the artifact reference with metadata
    artifact = future.result()
    print(f"Artifact type: {type(artifact)}")

    # 3. Use .load() to get the actual value
    # This gives you the integer 42
    value = future.load()
    calculated = value + 10
    print(f"Loaded value: {value}, plus 10 = {calculated}")

    # 4. Pass the future directly to a step
    # ZenML handles the artifact passing automatically
    double_value(future)


if __name__ == "__main__":
    async2_pipeline()
