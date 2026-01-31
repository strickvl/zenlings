"""
Advanced Mapping - Exercise 4: Solution

Complex workflows combine multiple patterns:
load for decisions, map for preprocessing, product for combinations.
"""

from zenml import pipeline, step
from zenml.execution.pipeline.dynamic.utils import unmapped


@step
def check_enabled() -> bool:
    """Check if processing is enabled."""
    return True


@step
def get_data_items() -> list[str]:
    """Get raw data items."""
    return ["item_a", "item_b", "item_c"]


@step
def get_processing_configs() -> list[str]:
    """Get different processing configurations."""
    return ["config_fast", "config_thorough"]


@step
def preprocess(item: str) -> str:
    """Preprocess a data item."""
    result = f"preprocessed_{item}"
    print(f"Preprocessing: {item} -> {result}")
    return result


@step
def process_with_config(item: str, config: str) -> str:
    """Process an item with a specific config."""
    result = f"{item}+{config}"
    print(f"Processing: {item} with {config} -> {result}")
    return result


@step
def aggregate_results(results: list[str]) -> None:
    """Aggregate all results."""
    print(f"\n=== Aggregated {len(results)} results ===")
    for r in results:
        print(f"  - {r}")


@step
def run_fallback() -> None:
    """Simple fallback when processing is disabled."""
    print("Processing disabled - running fallback")


@pipeline(dynamic=True)
def advanced4_pipeline():
    # SOLUTION:

    # 1. Check if enabled and load the result
    is_enabled = check_enabled()
    is_enabled_value = is_enabled.load()

    # 2. Branch based on the loaded value
    if is_enabled_value:
        # a. Get data and configs
        items = get_data_items()      # 3 items
        configs = get_processing_configs()  # 2 configs

        # b. Preprocess each item (3 preprocessing steps)
        preprocessed = preprocess.map(item=items)

        # c. Process all combinations (3 items × 2 configs = 6 processing steps)
        results = process_with_config.product(
            item=preprocessed,
            config=configs
        )

        # d. Aggregate
        aggregate_results(results)

    else:
        # 3. Fallback
        run_fallback()


if __name__ == "__main__":
    advanced4_pipeline()
