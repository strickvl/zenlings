"""
The Product Pattern - Exercise 2: Solution

Hyperparameter search is a perfect use case for .product().
Each axis of your search space becomes an input to .product().
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_learning_rates() -> list[float]:
    """Define learning rates to try."""
    return [0.001, 0.01, 0.1]


@step(enable_cache=False)
def get_batch_sizes() -> list[int]:
    """Define batch sizes to try."""
    return [16, 32]


@step(enable_cache=False)
def train_model(lr: float, batch_size: int) -> float:
    """
    Simulate training a model.
    Returns a fake accuracy score based on hyperparameters.
    """
    import random
    random.seed(int(lr * 10000) + batch_size)

    base = 0.7
    lr_bonus = 0.15 if lr == 0.01 else 0.05
    batch_bonus = 0.05 if batch_size == 32 else 0.02

    accuracy = base + lr_bonus + batch_bonus + random.uniform(-0.02, 0.02)
    print(f"lr={lr}, batch_size={batch_size} -> accuracy={accuracy:.4f}")
    return round(accuracy, 4)


@step(enable_cache=False)
def find_best(accuracies: list[float]) -> None:
    """Find and print the best accuracy."""
    best = max(accuracies)
    print(f"\nBest accuracy: {best:.4f}")
    print(f"Total experiments: {len(accuracies)}")


@pipeline(dynamic=True)
def product2_pipeline():
    # SOLUTION:
    # 1. Get hyperparameter ranges
    learning_rates = get_learning_rates()  # 3 values
    batch_sizes = get_batch_sizes()        # 2 values

    # 2. Use .product() to try all 3 × 2 = 6 combinations
    accuracies = train_model.product(lr=learning_rates, batch_size=batch_sizes)

    # 3. Find the best result
    find_best(accuracies)


if __name__ == "__main__":
    product2_pipeline()
