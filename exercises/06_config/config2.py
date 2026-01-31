"""
Configuration - Exercise 2: Understanding Runtime Modes

CONCEPT: Steps can run in different runtime modes:
         - "inline": Runs in the orchestration environment (fast, no isolation)
         - "isolated": Runs in a separate container (slower, but isolated)

         @step(runtime="inline")   # Quick operations
         @step(runtime="isolated") # Heavy computation, needs isolation

         Use inline for:
         - Quick decisions and routing logic
         - Loading small amounts of data
         - Orchestration control flow

         Use isolated for:
         - Heavy computation (training, inference)
         - Steps that need specific dependencies
         - Parallel workloads that benefit from distribution

NOTE: On the local orchestrator, both modes behave similarly.
      The difference matters on Kubernetes and cloud orchestrators.

TASK: Mark the appropriate runtime mode for each step based on its purpose.
"""

from zenml import pipeline, step


# TODO: Add runtime="inline" - this is a quick routing decision
@step
def decide_processing_mode(data_size: int) -> str:
    """Decide how to process based on data size."""
    if data_size > 1000:
        return "heavy"
    return "light"


# TODO: Add runtime="inline" - this just loads a small config
@step
def load_config() -> dict:
    """Load processing configuration."""
    return {"threshold": 0.5, "max_items": 100}


# TODO: Add runtime="isolated" - this is heavy computation
@step
def heavy_processing(data: list[int], config: dict) -> float:
    """Heavy computation that benefits from isolation."""
    # Simulate heavy work
    import time
    time.sleep(0.5)
    result = sum(data) * config["threshold"]
    print(f"Heavy processing complete: {result}")
    return result


# TODO: Add runtime="isolated" - this is also heavy computation
@step
def light_processing(data: list[int], config: dict) -> float:
    """Light computation."""
    result = sum(data) / len(data) if data else 0
    print(f"Light processing complete: {result}")
    return result


@step
def get_sample_data() -> list[int]:
    """Get sample data."""
    return list(range(100))


@pipeline(dynamic=True)
def config2_pipeline():
    data = get_sample_data()
    config = load_config()

    # Decide processing mode based on data size
    data_loaded = data.load()
    mode = decide_processing_mode(len(data_loaded))
    mode_value = mode.load()

    # Route to appropriate processor
    if mode_value == "heavy":
        heavy_processing(data, config)
    else:
        light_processing(data, config)


if __name__ == "__main__":
    config2_pipeline()
