"""
Advanced Mapping - Exercise 1: Broadcasting with unmapped()

CONCEPT: When using .map(), sometimes you want one input to be split across
         calls, but another input to be passed to ALL calls unchanged.

         Use unmapped() to "broadcast" a value to all mapped calls:
           step.map(item=items, config=unmapped(shared_config))

         Result: Each call gets one item, but ALL calls get the FULL config.

THE BUG: The config is being split instead of broadcast.

FIX: Import and use unmapped() to broadcast the config to all calls.
"""

from zenml import pipeline, step
# TODO: Import unmapped from the correct location
# from zenml.execution.pipeline.dynamic.utils import unmapped


@step
def get_items() -> list[int]:
    """Get items to process."""
    return [1, 2, 3, 4, 5]


@step
def get_config() -> dict:
    """Get shared configuration."""
    return {"multiplier": 10, "prefix": "Result"}


@step
def process_with_config(item: int, config: dict) -> str:
    """Process an item using the shared config."""
    result = item * config["multiplier"]
    output = f"{config['prefix']}: {item} × {config['multiplier']} = {result}"
    print(output)
    return output


@step
def show_results(results: list[str]) -> None:
    """Show all results."""
    print("\n=== All Results ===")
    for r in results:
        print(f"  {r}")


@pipeline(dynamic=True)
def advanced1_pipeline():
    items = get_items()    # 5 items
    config = get_config()  # 1 config dict

    # BUG: This treats config as a list to be split, but it's a single dict!
    # We need to use unmapped() to broadcast config to ALL calls
    results = process_with_config.map(item=items, config=config)

    show_results(results)


if __name__ == "__main__":
    advanced1_pipeline()
