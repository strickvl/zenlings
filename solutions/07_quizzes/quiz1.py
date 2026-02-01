"""
Quiz 1: Solution

Combines loading, conditionals, and mapping in one pipeline.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_items() -> list[int]:
    """Returns items to process."""
    return [10, 20, 30, 40, 50]


@step(enable_cache=False)
def check_threshold() -> bool:
    """Check if we have enough items (threshold: 3)."""
    return True


@step(enable_cache=False)
def process_item(x: int) -> int:
    """Process a single item."""
    result = x * 2
    print(f"Processed {x} -> {result}")
    return result


@step(enable_cache=False)
def fallback() -> str:
    """Fallback when not enough data."""
    message = "Not enough data - running fallback logic"
    print(message)
    return message


@step(enable_cache=False)
def verify(condition_was_true: bool, expected_results: list[int] | None = None) -> None:
    """Verification step."""
    if condition_was_true:
        expected = [20, 40, 60, 80, 100]
        assert expected_results == expected, f"Expected {expected}, got {expected_results}"
        print("✅ Quiz passed! Items were processed correctly.")
    else:
        print("✅ Quiz passed! Fallback was executed correctly.")


@pipeline(dynamic=True)
def quiz1_pipeline():
    # SOLUTION:
    # 1. Get items and check threshold
    items = get_items()
    should_process = check_threshold()

    # 2. Load the boolean to use in Python if
    should_process_value = should_process.load()

    # 3 & 4. Branch based on condition
    if should_process_value:
        # Map to process all items
        results = process_item.map(x=items)
        # Load to get the list
        results_data = results.load()
        # Verify with the results
        verify(True, results_data)
    else:
        # Run fallback
        fallback()
        # Verify without results
        verify(False)


if __name__ == "__main__":
    quiz1_pipeline()
