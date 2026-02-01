"""
Advanced Mapping - Exercise 3: Solution

Use .unpack() to split multi-output map results into separate lists.
Each output position becomes its own list.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_full_names() -> list[str]:
    """Get a list of full names."""
    return ["Alice Smith", "Bob Jones", "Carol White"]


@step(enable_cache=False)
def split_name(full_name: str) -> tuple[str, str]:
    """Split a full name into first and last."""
    parts = full_name.split()
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    print(f"Split '{full_name}' -> first='{first}', last='{last}'")
    return first, last


@step(enable_cache=False)
def process_first_names(names: list[str]) -> None:
    """Process all first names."""
    print(f"\nFirst names: {names}")


@step(enable_cache=False)
def process_last_names(names: list[str]) -> None:
    """Process all last names."""
    print(f"Last names: {names}")


@pipeline(dynamic=True)
def advanced3_pipeline():
    full_names = get_full_names()

    # SOLUTION:
    # 1. Map to split each name (returns tuple[str, str] for each)
    results = split_name.map(full_name=full_names)

    # 2. Unpack into separate lists
    # first_names gets all the first tuple elements
    # last_names gets all the second tuple elements
    first_names, last_names = results.unpack()

    # 3 & 4. Process each list separately
    process_first_names(first_names)
    process_last_names(last_names)


if __name__ == "__main__":
    advanced3_pipeline()
