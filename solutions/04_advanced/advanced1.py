"""
Advanced Mapping - Exercise 1: Solution

Use unmapped() to broadcast a value to all mapped calls.
The unmapped input is passed in full to every call.
"""

from zenml import pipeline, step
from zenml.execution.pipeline.dynamic.utils import unmapped


@step(enable_cache=False)
def get_items() -> list[int]:
    """Get items to process."""
    return [1, 2, 3, 4, 5]


@step(enable_cache=False)
def get_config() -> dict:
    """Get shared configuration."""
    return {"multiplier": 10, "prefix": "Result"}


@step(enable_cache=False)
def process_with_config(item: int, config: dict) -> str:
    """Process an item using the shared config."""
    result = item * config["multiplier"]
    output = f"{config['prefix']}: {item} × {config['multiplier']} = {result}"
    print(output)
    return output


@step(enable_cache=False)
def show_results(results: list[str]) -> None:
    """Show all results."""
    print("\n=== All Results ===")
    for r in results:
        print(f"  {r}")


@pipeline(dynamic=True)
def advanced1_pipeline():
    items = get_items()    # 5 items
    config = get_config()  # 1 config dict

    # SOLUTION: Use unmapped() to broadcast config to all calls
    # Each call receives: one item from items, the FULL config dict
    results = process_with_config.map(item=items, config=unmapped(config))

    show_results(results)


if __name__ == "__main__":
    advanced1_pipeline()
