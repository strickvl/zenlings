"""
Advanced Mapping - Exercise 2: Selective Processing with .chunk()

CONCEPT: Sometimes you need to selectively process only SOME items based
         on their values. Use .chunk(index) to get an artifact reference
         for a specific element.

         Pattern:
           items = create_list()              # Artifact with item_count
           items_data = items.load()          # Load to examine values
           for i, val in enumerate(items_data):
               if some_condition(val):
                   chunk = items.chunk(i)     # Get artifact reference
                   process(chunk)             # Pass to step

TASK: Complete the pipeline to:
      1. Get numbers and load them
      2. Loop through and find numbers > 5
      3. Use .chunk(i) to pass only large numbers to process_large()
      4. Report how many were processed
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_numbers() -> list[int]:
    """Get a list of numbers."""
    return [2, 8, 3, 12, 1, 9, 4, 15]


@step(enable_cache=False)
def process_large(n: int) -> int:
    """Process a large number (> 5)."""
    result = n * 100
    print(f"Processing large number {n} -> {result}")
    return result


@step(enable_cache=False)
def report(count: int) -> None:
    """Report how many large numbers were found."""
    print(f"\nProcessed {count} large numbers (> 5)")


@pipeline(dynamic=True)
def advanced2_pipeline():
    numbers = get_numbers()

    # TODO: Complete this pipeline
    # 1. Load the numbers to examine their values
    # 2. Loop through with enumerate
    # 3. For numbers > 5, use numbers.chunk(i) to get the artifact reference
    # 4. Pass the chunk to process_large()
    # 5. Count how many were processed and call report()

    pass


if __name__ == "__main__":
    advanced2_pipeline()
