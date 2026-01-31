"""
Async Execution - Exercise 3: Dependencies with after=[]

CONCEPT: Use after=[] to create explicit step dependencies.
         A step with after=[f1, f2] waits for both f1 and f2 to complete
         before starting, even if it doesn't use their outputs.

         This is useful when:
         - A step needs side effects from previous steps (file creation, etc.)
         - You want to control execution order explicitly
         - A step should only run after others complete

TASK: Complete the pipeline where:
      1. Two setup steps run in parallel
      2. A main step waits for BOTH setups before running
      3. A cleanup step runs after the main step
"""

from zenml import pipeline, step


@step
def setup_database() -> str:
    """Set up the database (simulated)."""
    print("Setting up database...")
    return "database_ready"


@step
def setup_cache() -> str:
    """Set up the cache (simulated)."""
    print("Setting up cache...")
    return "cache_ready"


@step
def run_main_process() -> str:
    """Run the main process (needs both setups complete)."""
    print("Running main process...")
    return "process_complete"


@step
def cleanup() -> None:
    """Clean up after main process."""
    print("Cleaning up...")


@pipeline(dynamic=True)
def async3_pipeline():
    # TODO: Complete this pipeline using after=[]
    #
    # 1. Submit setup_database and setup_cache in parallel
    # 2. Submit run_main_process with after=[db_future, cache_future]
    #    so it waits for both setups
    # 3. Submit cleanup with after=[main_future] so it runs last

    pass


if __name__ == "__main__":
    async3_pipeline()
