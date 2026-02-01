"""
The Map Pattern - Exercise 1: Solution

The .map() method is called on the step, not the artifact.
Syntax: step.map(parameter_name=artifact)
"""

from zenml import pipeline, step


@step(enable_cache=False)
def create_numbers() -> list[int]:
    """Create a list of numbers to process."""
    return [1, 2, 3, 4, 5]


@step(enable_cache=False)
def double(x: int) -> int:
    """Double a number."""
    result = x * 2
    print(f"{x} * 2 = {result}")
    return result


@pipeline(dynamic=True)
def map1_pipeline():
    numbers = create_numbers()

    # SOLUTION: Call .map() on the step, not the artifact
    # The parameter name (x) must match the step's parameter
    results = double.map(x=numbers)

    print("Mapping complete!")


if __name__ == "__main__":
    map1_pipeline()
