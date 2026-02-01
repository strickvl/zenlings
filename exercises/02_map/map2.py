"""
The Map Pattern - Exercise 2: Accessing Map Results

CONCEPT: The result of .map() is a MapResultsFuture, not raw data.
         To get the actual results, you can:
         - Call .load() to get all results as a list
         - Iterate over individual futures

TASK: Complete the pipeline to:
      1. Map over the numbers to triple each one
      2. Load all the results
      3. Print the sum of all results
"""

from zenml import pipeline, step


@step(enable_cache=False)
def create_numbers() -> list[int]:
    """Create a list of numbers."""
    return [1, 2, 3, 4, 5]


@step(enable_cache=False)
def triple(x: int) -> int:
    """Triple a number."""
    result = x * 3
    print(f"{x} * 3 = {result}")
    return result


@step(enable_cache=False)
def print_sum(total: int) -> None:
    """Print the sum."""
    print(f"Sum of all tripled numbers: {total}")


@pipeline(dynamic=True)
def map2_pipeline():
    numbers = create_numbers()

    # TODO: Complete this pipeline
    # 1. Use triple.map() to triple each number
    # 2. Load the results to get a list of integers
    # 3. Calculate the sum
    # 4. Call print_sum() with the total

    pass


if __name__ == "__main__":
    map2_pipeline()
