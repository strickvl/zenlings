"""
Loading Artifacts - Exercise 4: Solution

The fix is to load the artifact ONCE, then reuse the loaded data.
Loading inside a loop is inefficient and can cause issues with
artifact tracking in production scenarios.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_numbers() -> list[int]:
    """Returns a list of numbers."""
    print("Fetching numbers from data source...")
    return [1, 2, 3, 4, 5]


@step(enable_cache=False)
def square(n: int) -> int:
    """Square a number."""
    result = n * n
    print(f"{n}² = {result}")
    return result


@pipeline(dynamic=True)
def load4_pipeline():
    numbers = get_numbers()

    # SOLUTION: Load ONCE, then use the loaded data
    numbers_data = numbers.load()

    for n in numbers_data:
        square(n)


if __name__ == "__main__":
    load4_pipeline()
