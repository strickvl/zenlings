"""
The Product Pattern - Exercise 3: Solution

Chaining .map() then .product() creates sophisticated data pipelines.
Preprocess with map, then train all combinations with product.
"""

from zenml import pipeline, step


@step
def get_raw_datasets() -> list[str]:
    """Get raw dataset names."""
    return ["sales_2023", "sales_2024"]


@step
def get_model_types() -> list[str]:
    """Get model types to train."""
    return ["linear", "tree", "neural"]


@step
def preprocess(dataset: str) -> str:
    """Preprocess a raw dataset."""
    processed = f"processed_{dataset}"
    print(f"Preprocessing {dataset} -> {processed}")
    return processed


@step
def train(model_type: str, dataset: str) -> float:
    """Train a model on a dataset."""
    import hashlib
    seed = int(hashlib.md5(f"{model_type}{dataset}".encode()).hexdigest()[:8], 16)
    accuracy = 0.7 + (seed % 30) / 100
    print(f"Training {model_type} on {dataset} -> {accuracy:.2f}")
    return accuracy


@step
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

    # SOLUTION:
    # Step 1: Preprocess each dataset (2 preprocessing steps)
    preprocessed_datasets = preprocess.map(dataset=raw_datasets)

    # Step 2: Train all model × dataset combinations
    # 3 models × 2 datasets = 6 training runs
    accuracies = train.product(model_type=model_types, dataset=preprocessed_datasets)

    # Step 3: Report results
    report_results(accuracies)


if __name__ == "__main__":
    product3_pipeline()
