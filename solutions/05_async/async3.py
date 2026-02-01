"""
Async Execution - Exercise 3: Solution

Use after=[] to create explicit dependencies between async steps.
The step waits for all specified futures before running.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def setup_database() -> str:
    """Set up the database (simulated)."""
    print("Setting up database...")
    return "database_ready"


@step(enable_cache=False)
def setup_cache() -> str:
    """Set up the cache (simulated)."""
    print("Setting up cache...")
    return "cache_ready"


@step(enable_cache=False)
def run_main_process() -> str:
    """Run the main process (needs both setups complete)."""
    print("Running main process...")
    return "process_complete"


@step(enable_cache=False)
def cleanup() -> None:
    """Clean up after main process."""
    print("Cleaning up...")


@pipeline(dynamic=True)
def async3_pipeline():
    # SOLUTION:
    # 1. Submit both setups in parallel
    db_future = setup_database.submit()
    cache_future = setup_cache.submit()
    # Both are running concurrently now!

    # 2. Main process waits for BOTH setups
    main_future = run_main_process.submit(after=[db_future, cache_future])

    # 3. Cleanup runs after main process completes
    cleanup.submit(after=[main_future])


if __name__ == "__main__":
    async3_pipeline()
