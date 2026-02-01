"""
Loading Artifacts - Exercise 3: Solution

Conditional execution uses loaded boolean values in Python if statements.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def check_data_valid() -> bool:
    """Check if the data passes validation."""
    print("Checking data validity...")
    return True


@step(enable_cache=False)
def process_data() -> str:
    """Process the valid data."""
    result = "Data processed successfully!"
    print(result)
    return result


@step(enable_cache=False)
def cleanup_invalid_data() -> str:
    """Handle invalid data."""
    result = "Cleaned up invalid data"
    print(result)
    return result


@pipeline(dynamic=True)
def load3_pipeline():
    # SOLUTION:
    # 1. Get the validation result artifact
    is_valid = check_data_valid()

    # 2. Load the boolean value
    is_valid_value = is_valid.load()

    # 3. Branch based on the loaded value
    if is_valid_value:
        process_data()
    else:
        cleanup_invalid_data()


if __name__ == "__main__":
    load3_pipeline()
