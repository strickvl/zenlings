"""
Loading Artifacts - Exercise 4: Debug the .load() Mistake

CONCEPT: A common mistake is loading an artifact in the wrong scope,
         or loading it multiple times when you should load once.

THE BUG: This pipeline has a subtle bug. It runs, but it's inefficient
         and might not work as expected in production scenarios.

TASK: Find and fix the bug. The pipeline should:
      - Load the items list ONCE
      - Use that loaded data in the loop
      - Not call .load() repeatedly inside the loop
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

    # BUG: There's something wrong with how we're using .load() here
    # This is inefficient and could cause issues!
    for i in range(len(numbers.load())):  # Loading in the condition
        n = numbers.load()[i]              # Loading again to get the item!
        square(n)


if __name__ == "__main__":
    load4_pipeline()
