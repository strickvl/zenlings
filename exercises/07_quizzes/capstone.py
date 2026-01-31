"""
Capstone Project: Hyperparameter Search Pipeline

Congratulations on making it to the final exercise! 🎉

In this capstone, you'll build a complete hyperparameter search pipeline
that demonstrates mastery of dynamic pipelines.

SCENARIO:
You're training a machine learning model and want to find the best
hyperparameters. You'll:

1. Define hyperparameter ranges (learning rates, batch sizes)
2. Use .product() to try all combinations
3. "Train" a model for each combination (simulated)
4. Collect results and find the best configuration

This is a REAL use case for dynamic pipelines in production ML systems!

REQUIREMENTS:
- Use at least 3 learning rates and 2 batch sizes (6+ experiments)
- Use .product() to create all combinations
- Find and print the best hyperparameter combination
- The verify step will check your implementation

BUILD THE PIPELINE FROM SCRATCH!
"""

from typing import Any
from zenml import pipeline, step


@step
def get_learning_rates() -> list[float]:
    """Get learning rates to try."""
    # TODO: Return a list of at least 3 learning rates
    # Example: [0.001, 0.01, 0.1]
    pass


@step
def get_batch_sizes() -> list[int]:
    """Get batch sizes to try."""
    # TODO: Return a list of at least 2 batch sizes
    # Example: [16, 32]
    pass


@step
def train_model(lr: float, batch_size: int) -> float:
    """
    Simulate training a model with given hyperparameters.
    Returns a simulated accuracy score.
    """
    # Simulated training - in real life this would train an actual model
    # The "best" config is lr=0.01, batch_size=32 (gives highest accuracy)
    import random
    random.seed(int(lr * 1000) + batch_size)

    base_accuracy = 0.7
    lr_bonus = 0.1 if lr == 0.01 else 0.05
    batch_bonus = 0.05 if batch_size == 32 else 0.02
    noise = random.uniform(-0.02, 0.02)

    accuracy = base_accuracy + lr_bonus + batch_bonus + noise
    print(f"Training with lr={lr}, batch_size={batch_size} -> accuracy={accuracy:.4f}")
    return round(accuracy, 4)


@step
def find_best(accuracies: list[float], learning_rates: list[float], batch_sizes: list[int]) -> dict[str, Any]:
    """Find the best hyperparameter combination."""
    # Create all combinations (same order as .product())
    configs = [(lr, bs) for lr in learning_rates for bs in batch_sizes]

    best_idx = accuracies.index(max(accuracies))
    best_config = configs[best_idx]

    result = {
        "best_accuracy": max(accuracies),
        "best_lr": best_config[0],
        "best_batch_size": best_config[1],
        "total_experiments": len(accuracies)
    }

    print(f"\n🏆 Best configuration found!")
    print(f"   Learning rate: {result['best_lr']}")
    print(f"   Batch size: {result['best_batch_size']}")
    print(f"   Accuracy: {result['best_accuracy']:.4f}")
    print(f"   Total experiments: {result['total_experiments']}")

    return result


@step
def verify_capstone(result: dict[str, Any]) -> None:
    """Verify the capstone was completed correctly."""
    assert result["total_experiments"] >= 6, "Need at least 3 LRs × 2 batch sizes = 6 experiments"
    assert result["best_accuracy"] > 0.8, "Best accuracy should be > 0.8"
    print("\n✅ CAPSTONE COMPLETE! You've mastered dynamic pipelines! 🎉")


@pipeline(dynamic=True)
def capstone_pipeline():
    """
    TODO: Build your hyperparameter search pipeline!

    Steps:
    1. Get learning rates and batch sizes (implement the steps above)
    2. Use train_model.product() to try all combinations
    3. Load the accuracies and the original hyperparameter lists
    4. Call find_best() with all the data
    5. Call verify_capstone() to check your work

    Good luck! 🚀
    """
    pass


if __name__ == "__main__":
    capstone_pipeline()
