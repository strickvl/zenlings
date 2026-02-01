"""
The Product Pattern - Exercise 2: Hyperparameter Grid Search

CONCEPT: .product() is perfect for hyperparameter search!
         Define ranges for each hyperparameter, then try all combinations.

TASK: Build a hyperparameter search pipeline from scratch that:
      1. Defines learning rates: [0.001, 0.01, 0.1]
      2. Defines batch sizes: [16, 32]
      3. Uses .product() to train with all 6 combinations
      4. Finds and prints the best configuration

NOTE: The train_model step is a simulation - it returns fake accuracy scores.
      In real life, this would train actual ML models!
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_learning_rates() -> list[float]:
    """Define learning rates to try."""
    # TODO: Return [0.001, 0.01, 0.1]
    pass


@step(enable_cache=False)
def get_batch_sizes() -> list[int]:
    """Define batch sizes to try."""
    # TODO: Return [16, 32]
    pass


@step(enable_cache=False)
def train_model(lr: float, batch_size: int) -> float:
    """
    Simulate training a model.
    Returns a fake accuracy score based on hyperparameters.
    (In real life, this would train an actual model!)
    """
    # Simulation: best config is lr=0.01, batch_size=32
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
    # TODO: Build the hyperparameter search pipeline
    # 1. Get learning rates and batch sizes
    # 2. Use train_model.product() to try all combinations
    # 3. Pass results to find_best()
    pass


if __name__ == "__main__":
    product2_pipeline()
