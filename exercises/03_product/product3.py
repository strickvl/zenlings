"""
The Product Pattern - Exercise 3: Combining Map and Product

CONCEPT: You can chain .map() and .product() in sophisticated workflows.
         Example: Preprocess each dataset, then train all model×dataset combinations.

SCENARIO: You have raw datasets that need preprocessing before training.
          - First: use .map() to preprocess each dataset
          - Then: use .product() to train each model on each preprocessed dataset

TASK: Complete the pipeline to:
      1. Map over raw_datasets to preprocess each one
      2. Product with model_types to train all combinations
      3. Report the results
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_raw_datasets() -> list[str]:
    """Get raw dataset names."""
    return ["sales_2023", "sales_2024"]


@step(enable_cache=False)
def get_model_types() -> list[str]:
    """Get model types to train."""
    return ["linear", "tree", "neural"]


@step(enable_cache=False)
def preprocess(dataset: str) -> str:
    """Preprocess a raw dataset."""
    processed = f"processed_{dataset}"
    print(f"Preprocessing {dataset} -> {processed}")
    return processed


@step(enable_cache=False)
def train(model_type: str, dataset: str) -> float:
    """Train a model on a dataset."""
    # Simulate training
    import hashlib
    seed = int(hashlib.md5(f"{model_type}{dataset}".encode()).hexdigest()[:8], 16)
    accuracy = 0.7 + (seed % 30) / 100
    print(f"Training {model_type} on {dataset} -> {accuracy:.2f}")
    return accuracy


@step(enable_cache=False)
def report_results(accuracies: list[float]) -> None:
    """Report training results."""
    print(f"\n=== Training Complete ===")
    print(f"Total experiments: {len(accuracies)}")
    print(f"Best accuracy: {max(accuracies):.2f}")
    print(f"Average accuracy: {sum(accuracies)/len(accuracies):.2f}")


@pipeline(dynamic=True)
def product3_pipeline():
    raw_datasets = get_raw_datasets()  # 2 datasets
    model_types = get_model_types()     # 3 models

    # TODO: Complete this pipeline
    # Step 1: Use preprocess.map() to preprocess each dataset
    # Step 2: Use train.product() with model_types and preprocessed datasets
    #         This should create 3 × 2 = 6 training runs
    # Step 3: Pass results to report_results()

    pass


if __name__ == "__main__":
    product3_pipeline()
