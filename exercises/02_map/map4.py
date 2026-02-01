"""
The Map Pattern - Exercise 4: Multiple Mapped Inputs

CONCEPT: When mapping with multiple inputs, they must have the SAME LENGTH.
         The i-th call receives the i-th element from each input.

         Example: items1=[1,2,3] and items2=['a','b','c']
         step.map(a=items1, b=items2) produces:
           - step(1, 'a')
           - step(2, 'b')
           - step(3, 'c')

TASK: Build a pipeline from scratch that:
      1. Creates a list of names
      2. Creates a list of ages (same length!)
      3. Maps over both to create greeting messages
      4. Prints all greetings
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_names() -> list[str]:
    """Get a list of names."""
    # TODO: Return a list of 3 names
    pass


@step(enable_cache=False)
def get_ages() -> list[int]:
    """Get a list of ages."""
    # TODO: Return a list of 3 ages (same length as names!)
    pass


@step(enable_cache=False)
def create_greeting(name: str, age: int) -> str:
    """Create a personalized greeting."""
    greeting = f"Hello {name}, you are {age} years old!"
    print(greeting)
    return greeting


@step(enable_cache=False)
def print_all_greetings(greetings: list[str]) -> None:
    """Print all greetings."""
    print("\n--- All Greetings ---")
    for g in greetings:
        print(f"  {g}")


@pipeline(dynamic=True)
def map4_pipeline():
    # TODO: Build the pipeline
    # 1. Get names and ages
    # 2. Use create_greeting.map() with BOTH inputs
    # 3. Pass results to print_all_greetings
    pass


if __name__ == "__main__":
    map4_pipeline()
