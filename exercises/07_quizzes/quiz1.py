"""
Quiz 1: Combining Concepts

This quiz tests your understanding of:
- Loading artifacts with .load()
- Conditional execution with if/else
- The map pattern with .map()

SCENARIO:
You're building a data processing pipeline that:
1. Checks if there's enough data to process (threshold check)
2. If yes: processes each item in parallel using .map()
3. If no: runs a single fallback step instead

IMPLEMENT the pipeline body below. The steps are provided.
"""

from zenml import pipeline, step


@step
def get_items() -> list[int]:
    """Returns items to process."""
    return [10, 20, 30, 40, 50]


@step
def check_threshold() -> bool:
    """Check if we have enough items (threshold: 3)."""
    # In real life, this might check database row count, file size, etc.
    return True  # We do have enough items


@step
def process_item(x: int) -> int:
    """Process a single item."""
    result = x * 2
    print(f"Processed {x} -> {result}")
    return result


@step
def fallback() -> str:
    """Fallback when not enough data."""
    message = "Not enough data - running fallback logic"
    print(message)
    return message


@step
def verify(condition_was_true: bool, expected_results: list[int] | None = None) -> None:
    """Verification step - DO NOT MODIFY."""
    if condition_was_true:
        expected = [20, 40, 60, 80, 100]
        assert expected_results == expected, f"Expected {expected}, got {expected_results}"
        print("✅ Quiz passed! Items were processed correctly.")
    else:
        print("✅ Quiz passed! Fallback was executed correctly.")


@pipeline(dynamic=True)
def quiz1_pipeline():
    """
    TODO: Implement this pipeline!

    Requirements:
    1. Get items and check threshold (call both steps)
    2. Load the threshold result to use in a Python if statement
    3. If threshold is True:
       - Use process_item.map() to process all items
       - Load the results
       - Call verify(True, results_data)
    4. If threshold is False:
       - Call fallback()
       - Call verify(False)
    """
    # Your code here!
    pass


if __name__ == "__main__":
    quiz1_pipeline()
