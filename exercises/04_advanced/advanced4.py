"""
Advanced Mapping - Exercise 4: Complex Workflow

CONCEPT: Real-world pipelines often combine multiple patterns:
         - .load() to make decisions
         - .map() for parallel processing
         - .product() for combinations
         - unmapped() for broadcasting
         - conditionals for branching

SCENARIO: You're building a data processing pipeline that:
          1. Checks if processing is enabled
          2. If enabled: preprocesses data, then processes with multiple configs
          3. If disabled: runs a simple fallback

TASK: Build this complete pipeline from scratch!
      The steps are provided - you need to wire them together.
"""

from zenml import pipeline, step
from zenml.execution.pipeline.dynamic.utils import unmapped


@step
def check_enabled() -> bool:
    """Check if processing is enabled."""
    return True  # Processing is enabled


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
    """
    TODO: Build this complex pipeline!

    Logic:
    1. Check if processing is enabled (load the result)
    2. If enabled:
       a. Get data items and configs
       b. Preprocess each item with .map()
       c. Process all item × config combinations with .product()
       d. Aggregate the results
    3. If not enabled:
       a. Run the fallback step
    """
    pass


if __name__ == "__main__":
    advanced4_pipeline()
