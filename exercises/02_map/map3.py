"""
The Map Pattern - Exercise 3: Passing Map Results Downstream

CONCEPT: You can pass a MapResultsFuture directly to a downstream step
         that expects a list! ZenML automatically waits for all mapped
         steps to complete and collects their outputs.

TASK: Complete the pipeline to:
      1. Map over words to get their lengths
      2. Pass the map results directly to find_longest()
      3. The find_longest step expects list[int] and finds the maximum
"""

from zenml import pipeline, step


@step
def get_words() -> list[str]:
    """Get a list of words."""
    return ["apple", "banana", "cherry", "date", "elderberry"]


@step
def get_length(word: str) -> int:
    """Get the length of a word."""
    length = len(word)
    print(f"'{word}' has {length} characters")
    return length


@step
def find_longest(lengths: list[int]) -> int:
    """Find the longest length."""
    longest = max(lengths)
    print(f"The longest word has {longest} characters")
    return longest


@pipeline(dynamic=True)
def map3_pipeline():
    words = get_words()

    # TODO: Complete this pipeline
    # 1. Use get_length.map() to get the length of each word
    # 2. Pass the map results directly to find_longest()
    #    (No need to .load() - ZenML handles the collection!)

    pass


if __name__ == "__main__":
    map3_pipeline()
