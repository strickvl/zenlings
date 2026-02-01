"""
The Map Pattern - Exercise 1: Your First .map()

CONCEPT: step.map(param=items) runs the step once for each element in items.
         This creates parallel step executions automatically!

THE BUG: The code tries to call .map() on the items instead of the step.

FIX: Call .map() on the step function, passing items as the parameter.
     The syntax is: step.map(param_name=artifact)
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

    # TODO: Fix this line
    # Wrong: artifact.map(step)
    # Right: step.map(param=artifact)
    results = numbers.map(double)  # <-- This is backwards!

    # Print that we're done
    print("Mapping complete!")


if __name__ == "__main__":
    map1_pipeline()
