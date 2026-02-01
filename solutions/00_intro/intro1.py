"""
Welcome to Zenlings! - Solution

This exercise already works! No changes needed.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def greet() -> str:
    """A simple greeting step."""
    message = "Hello from ZenML! 👋"
    print(message)
    return message


@step(enable_cache=False)
def celebrate() -> None:
    """Celebrate completing the first exercise!"""
    print("🎉 Congratulations! Your first ZenML pipeline ran successfully!")
    print("Press 'n' to continue to the next exercise.")


@pipeline
def hello_pipeline():
    """Your first ZenML pipeline."""
    greeting = greet()
    celebrate()


if __name__ == "__main__":
    hello_pipeline()
