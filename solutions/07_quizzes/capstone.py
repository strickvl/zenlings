"""
Capstone Project: Solution

A complete hyperparameter search pipeline using .product().
This demonstrates real-world dynamic pipeline usage.
"""

from typing import Any
from zenml import pipeline, step


@step(enable_cache=False)
def get_learning_rates() -> list[float]:
    """Get learning rates to try."""
    # SOLUTION: Return 3 learning rates
    return [0.001, 0.01, 0.1]


@step(enable_cache=False)
def get_batch_sizes() -> list[int]:
    """Get batch sizes to try."""
    # SOLUTION: Return 2 batch sizes
    return [16, 32]


@step(enable_cache=False)
def train_model(lr: float, batch_size: int) -> float:
    """Simulate training a model with given hyperparameters."""
    import random
    random.seed(int(lr * 1000) + batch_size)

    base_accuracy = 0.7
    lr_bonus = 0.1 if lr == 0.01 else 0.05
    batch_bonus = 0.05 if batch_size == 32 else 0.02
    noise = random.uniform(-0.02, 0.02)

    accuracy = base_accuracy + lr_bonus + batch_bonus + noise
    print(f"Training with lr={lr}, batch_size={batch_size} -> accuracy={accuracy:.4f}")
    return round(accuracy, 4)


@step(enable_cache=False)
def find_best(accuracies: list[float], learning_rates: list[float], batch_sizes: list[int]) -> dict[str, Any]:
    """Find the best hyperparameter combination."""
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


@step(enable_cache=False)
def verify_capstone(result: dict[str, Any]) -> None:
    """Verify the capstone was completed correctly."""
    assert result["total_experiments"] >= 6, "Need at least 3 LRs × 2 batch sizes = 6 experiments"
    assert result["best_accuracy"] > 0.8, "Best accuracy should be > 0.8"
    print("\n✅ CAPSTONE COMPLETE! You've mastered dynamic pipelines! 🎉")


@pipeline(dynamic=True)
def capstone_pipeline():
    # SOLUTION:
    # 1. Get hyperparameter ranges
    learning_rates = get_learning_rates()  # 3 values
    batch_sizes = get_batch_sizes()        # 2 values

    # 2. Use .product() for all combinations (3 × 2 = 6 experiments)
    accuracies = train_model.product(lr=learning_rates, batch_size=batch_sizes)

    # 3. Load all the data we need
    accuracies_data = accuracies.load()
    lr_data = learning_rates.load()
    bs_data = batch_sizes.load()

    # 4. Find the best configuration
    result = find_best(accuracies_data, lr_data, bs_data)

    # 5. Verify completion
    verify_capstone(result)


if __name__ == "__main__":
    capstone_pipeline()
