"""
Configuration - Exercise 2: Solution

Use runtime="inline" for quick orchestration logic.
Use runtime="isolated" for heavy computation.
"""

from zenml import pipeline, step


# SOLUTION: Inline for quick routing decisions
@step(runtime="inline")
def decide_processing_mode(data_size: int) -> str:
    """Decide how to process based on data size."""
    if data_size > 1000:
        return "heavy"
    return "light"


# SOLUTION: Inline for loading small configs
@step(runtime="inline")
def load_config() -> dict:
    """Load processing configuration."""
    return {"threshold": 0.5, "max_items": 100}


# SOLUTION: Isolated for heavy computation
@step(runtime="isolated")
def heavy_processing(data: list[int], config: dict) -> float:
    """Heavy computation that benefits from isolation."""
    import time
    time.sleep(0.5)
    result = sum(data) * config["threshold"]
    print(f"Heavy processing complete: {result}")
    return result


# SOLUTION: Could be inline or isolated depending on actual workload
@step(runtime="isolated")
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
    config = load_config()  # Now runs inline (fast!)

    # Decide processing mode - also inline (fast!)
    data_loaded = data.load()
    mode = decide_processing_mode(len(data_loaded))
    mode_value = mode.load()

    # Heavy steps run isolated (can be distributed on K8s)
    if mode_value == "heavy":
        heavy_processing(data, config)
    else:
        light_processing(data, config)


if __name__ == "__main__":
    config2_pipeline()
