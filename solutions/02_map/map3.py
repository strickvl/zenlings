"""
The Map Pattern - Exercise 3: Solution

MapResultsFuture can be passed directly to steps expecting lists.
ZenML automatically waits for completion and collects outputs.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_words() -> list[str]:
    """Get a list of words."""
    return ["apple", "banana", "cherry", "date", "elderberry"]


@step(enable_cache=False)
def get_length(word: str) -> int:
    """Get the length of a word."""
    length = len(word)
    print(f"'{word}' has {length} characters")
    return length


@step(enable_cache=False)
def find_longest(lengths: list[int]) -> int:
    """Find the longest length."""
    longest = max(lengths)
    print(f"The longest word has {longest} characters")
    return longest


@pipeline(dynamic=True)
def map3_pipeline():
    words = get_words()

    # SOLUTION:
    # 1. Map to get lengths
    lengths = get_length.map(word=words)

    # 2. Pass directly to downstream step - no .load() needed!
    # ZenML will wait for all mapped steps and collect the results
    find_longest(lengths)


if __name__ == "__main__":
    map3_pipeline()
