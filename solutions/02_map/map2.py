"""
The Map Pattern - Exercise 2: Solution

MapResultsFuture.load() returns a list of all the mapped step outputs.
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

    # SOLUTION:
    # 1. Map to triple each number
    results = triple.map(x=numbers)

    # 2. Load all results as a list
    results_data = results.load()  # [3, 6, 9, 12, 15]

    # 3. Calculate sum
    total = sum(results_data)

    # 4. Print the sum
    print_sum(total)


if __name__ == "__main__":
    map2_pipeline()
