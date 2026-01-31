"""
Async Execution - Exercise 1: Solution

Use .submit() to enable parallel step execution.
Steps run concurrently instead of sequentially.
"""

from zenml import pipeline, step
import time


@step
def slow_step_a() -> str:
    """A slow step that takes time."""
    print("Step A starting...")
    time.sleep(1)
    print("Step A done!")
    return "Result A"


@step
def slow_step_b() -> str:
    """Another slow step that takes time."""
    print("Step B starting...")
    time.sleep(1)
    print("Step B done!")
    return "Result B"


@step
def combine_results(a: str, b: str) -> str:
    """Combine results from both steps."""
    result = f"Combined: {a} + {b}"
    print(result)
    return result


@pipeline(dynamic=True)
def async1_pipeline():
    # SOLUTION: Use .submit() for parallel execution
    future_a = slow_step_a.submit()  # Starts immediately
    future_b = slow_step_b.submit()  # Also starts immediately (parallel!)

    # Both are running concurrently now
    # When we pass futures to combine_results, ZenML waits automatically
    combine_results(future_a, future_b)


if __name__ == "__main__":
    async1_pipeline()
