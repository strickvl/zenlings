"""
Welcome to Zenlings! 🎉

This is your first exercise. It's a simple ZenML pipeline that already works.
Run it to see how a basic pipeline executes.

GOAL: Just run this exercise to see it work!
      Press 'n' to continue to the next exercise.

NOTE: This is a STATIC pipeline (not dynamic yet). We'll make it dynamic soon!
"""

from zenml import pipeline, step


@step
def greet() -> str:
    """A simple greeting step."""
    message = "Hello from ZenML! 👋"
    print(message)
    return message


@step
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
