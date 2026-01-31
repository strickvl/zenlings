"""
The Map Pattern - Exercise 4: Solution

When mapping with multiple inputs, they're zipped together.
The i-th call gets the i-th element from each input.
"""

from zenml import pipeline, step


@step
def get_names() -> list[str]:
    """Get a list of names."""
    return ["Alice", "Bob", "Charlie"]


@step
def get_ages() -> list[int]:
    """Get a list of ages."""
    return [25, 30, 35]


@step
def create_greeting(name: str, age: int) -> str:
    """Create a personalized greeting."""
    greeting = f"Hello {name}, you are {age} years old!"
    print(greeting)
    return greeting


@step
def print_all_greetings(greetings: list[str]) -> None:
    """Print all greetings."""
    print("\n--- All Greetings ---")
    for g in greetings:
        print(f"  {g}")


@pipeline(dynamic=True)
def map4_pipeline():
    # SOLUTION:
    # 1. Get both lists
    names = get_names()
    ages = get_ages()

    # 2. Map with multiple inputs - they're zipped together
    # Creates: create_greeting("Alice", 25), create_greeting("Bob", 30), ...
    greetings = create_greeting.map(name=names, age=ages)

    # 3. Pass to downstream step
    print_all_greetings(greetings)


if __name__ == "__main__":
    map4_pipeline()
