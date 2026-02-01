"""
Async Execution - Exercise 1: Your First .submit()

CONCEPT: .submit() returns IMMEDIATELY with a future, enabling parallel execution.
         Without submit, steps run sequentially.
         With submit, multiple steps can run concurrently!

         Pattern:
           future1 = step1.submit()  # Starts immediately, returns future
           future2 = step2.submit()  # Also starts immediately (parallel!)
           # Both are running concurrently now
           result1 = future1.load()  # Wait for step1 and get data
           result2 = future2.load()  # Wait for step2 and get data

THE BUG: The steps are called directly instead of with .submit(),
         so they run sequentially instead of in parallel.

FIX: Use .submit() to enable parallel execution.
"""

from zenml import pipeline, step
import time


@step(enable_cache=False)
def slow_step_a() -> str:
    """A slow step that takes time."""
    print("Step A starting...")
    time.sleep(1)  # Simulate work
    print("Step A done!")
    return "Result A"


@step(enable_cache=False)
def slow_step_b() -> str:
    """Another slow step that takes time."""
    print("Step B starting...")
    time.sleep(1)  # Simulate work
    print("Step B done!")
    return "Result B"


@step(enable_cache=False)
def combine_results(a: str, b: str) -> str:
    """Combine results from both steps."""
    result = f"Combined: {a} + {b}"
    print(result)
    return result


@pipeline(dynamic=True)
def async1_pipeline():
    # BUG: These run sequentially (A finishes, then B starts)
    # Total time: ~2 seconds
    result_a = slow_step_a()
    result_b = slow_step_b()

    # TODO: Fix the above to use .submit() for parallel execution
    # With submit: A and B run at the same time
    # Total time: ~1 second (parallel!)

    combine_results(result_a, result_b)


if __name__ == "__main__":
    async1_pipeline()
