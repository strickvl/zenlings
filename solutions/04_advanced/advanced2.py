"""
Advanced Mapping - Exercise 2: Solution

Use .chunk(i) for selective processing based on loaded values.
This gives you artifact references for specific elements.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_numbers() -> list[int]:
    """Get a list of numbers."""
    return [2, 8, 3, 12, 1, 9, 4, 15]


@step(enable_cache=False)
def process_large(n: int) -> int:
    """Process a large number (> 5)."""
    result = n * 100
    print(f"Processing large number {n} -> {result}")
    return result


@step(enable_cache=False)
def report(count: int) -> None:
    """Report how many large numbers were found."""
    print(f"\nProcessed {count} large numbers (> 5)")


@pipeline(dynamic=True)
def advanced2_pipeline():
    numbers = get_numbers()

    # SOLUTION:
    # 1. Load to examine values
    numbers_data = numbers.load()

    # 2. Track how many we process
    count = 0

    # 3. Loop and selectively process
    for i, n in enumerate(numbers_data):
        if n > 5:
            # Get artifact reference for this specific element
            chunk = numbers.chunk(i)
            # Pass to step (artifact reference, not raw data)
            process_large(chunk)
            count += 1

    # 4. Report
    report(count)


if __name__ == "__main__":
    advanced2_pipeline()
