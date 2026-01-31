"""
Advanced Mapping - Exercise 3: Unpacking Multi-Output Steps

CONCEPT: When a mapped step returns multiple outputs (a tuple), you can
         use .unpack() to split the MapResultsFuture into separate lists.

         Example:
           @step
           def compute(x: int) -> tuple[int, int]:
               return x * 2, x * 3

           results = compute.map(x=items)
           doubles, triples = results.unpack()
           # doubles = list of first outputs (x * 2)
           # triples = list of second outputs (x * 3)

TASK: Complete the pipeline to:
      1. Map split_name over a list of full names
      2. Unpack the results into first_names and last_names
      3. Pass each list to its respective processing step
"""

from zenml import pipeline, step


@step
def get_full_names() -> list[str]:
    """Get a list of full names."""
    return ["Alice Smith", "Bob Jones", "Carol White"]


@step
def split_name(full_name: str) -> tuple[str, str]:
    """Split a full name into first and last."""
    parts = full_name.split()
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    print(f"Split '{full_name}' -> first='{first}', last='{last}'")
    return first, last


@step
def process_first_names(names: list[str]) -> None:
    """Process all first names."""
    print(f"\nFirst names: {names}")


@step
def process_last_names(names: list[str]) -> None:
    """Process all last names."""
    print(f"Last names: {names}")


@pipeline(dynamic=True)
def advanced3_pipeline():
    full_names = get_full_names()

    # TODO: Complete this pipeline
    # 1. Use split_name.map() to split each name
    # 2. Use .unpack() to separate first and last names
    # 3. Pass first_names to process_first_names()
    # 4. Pass last_names to process_last_names()

    pass


if __name__ == "__main__":
    advanced3_pipeline()
