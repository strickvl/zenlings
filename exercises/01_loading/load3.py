"""
Loading Artifacts - Exercise 3: Conditional Execution

CONCEPT: You can use loaded boolean values in Python if statements
         to conditionally execute different branches of your pipeline.

SCENARIO: You're building a data pipeline that checks if data is valid
          before processing. If invalid, it should run a cleanup step instead.

TASK: Complete the pipeline to:
      1. Check if the data is valid (call check_data_valid())
      2. Load the boolean result
      3. If valid: call process_data()
      4. If not valid: call cleanup_invalid_data()
"""

from zenml import pipeline, step


@step(enable_cache=False)
def check_data_valid() -> bool:
    """Check if the data passes validation."""
    # Simulating a validation check
    print("Checking data validity...")
    return True  # Data is valid


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
    # TODO: Complete this pipeline
    # 1. Call check_data_valid() to get the validation result
    # 2. Load the boolean result
    # 3. Use an if statement to branch:
    #    - If valid: call process_data()
    #    - If not valid: call cleanup_invalid_data()
    pass


if __name__ == "__main__":
    load3_pipeline()
